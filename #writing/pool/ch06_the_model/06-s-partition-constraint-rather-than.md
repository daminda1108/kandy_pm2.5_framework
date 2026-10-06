## The partition, which is a constraint rather than a choice {#s-partition-constraint-rather-than}

The decomposition is only useful to a decision if the split between local and regional is
credible, and for most of this project's history it was not. The value was taken from source
apportionment literature and sat near a quarter.

The argument that replaced it is short. Local sources emit continuously, and rain changes removal
rather than emission, so at an emitting location some locally generated material is present at
every hour. The decomposition's increment is then required to be non-negative, the background can
never reach the total, and **a background at or above the total is not an unusual hour but an
over-estimated background**. Since *B* is flat within a day, the constraint has a closed form: cap
each day at (1 − *F*~min~) times that day's minimum hourly total.

**This is a non-negative local-contribution constraint, and it should be called that rather than a
physical theorem.** Continuous emission is a statement about sources; *T* − *B* is a statement about
a constructed decomposition, and the two are not the same object. Transport, mixing, deposition,
secondary formation and a background that is itself built rather than measured all sit between
them, so continuous emission does not by itself prove that this particular residual must be
positive in every hour. What it does is make a negative residual far more readily explained by an
over-estimated background than by a real state of the atmosphere, which is enough to justify the
constraint as a modelling choice. It is imposed on those grounds, and {{ref:s-partition-constraint-rather-than}} reports how much
the resulting fraction moves when the choice is varied.

Before the constraint, the background exceeded the total in
{{claim:field.precap_excess_lo}} to {{claim:field.precap_excess_hi}} per cent of hours, averaging
{{claim:field.precap_excess_mean}}. In each such hour the field rendered flat and reported a zero
local share at the traffic core. After the constraint the residual is at worst
{{claim:field.postcap_excess_max}} per cent in any year, and every remaining case is an hour
where the anchor itself returned a negative total, which no constraint on the background can
repair.

Across the anchored years the local fraction is **{{claim:partition.f}}**, ranging
{{claim:partition.f_lo}} to {{claim:partition.f_hi}}.

**The result does not depend on the free parameter.** Sweeping *F*~min~ from zero to
{{claim:field.f_sweep_param_hi}}, a fourfold change, moves the fraction from
{{claim:field.f_sweep_lo}} to {{claim:field.f_sweep_hi}}. The value used was chosen as the
smallest that removes the defect, before the resulting fraction was known. Nor does it depend
much on the form of the constraint, which is the more searching test. The production form uses a
calendar-day minimum and gives {{claim:field.f_form_calendar}}. Replacing it with a centred
rolling twenty-four hour minimum gives {{claim:field.f_form_roll24}}, and doubling that window to
forty-eight hours gives {{claim:field.f_form_roll48}}. The answer is stable across constraint
forms that respect the daily structure of *B*, and drifts only when the window exceeds the
timescale on which *B* is defined.

The sweep and the constraint-form figures come from an independent reimplementation of the
constraint and not from the production code path. The production-path sweep does survive as an
artefact, and it is drawn beside the reimplementation in the figure below: the two differ by
less than a hundredth at every value of *F*~min~, the reimplementation reading slightly higher,
and they agree on the conclusion. The text quotes the reimplementation because it also covers
the constraint forms, which the production sweep does not.

The forty-eight hour form is the one that moves, from {{claim:field.f_form_calendar}} to
{{claim:field.f_form_roll48}}, and it is reported rather than excluded as an outlier. That is a
change of about a tenth in relative terms and it is the honest upper end of the sensitivity. The
reason it drifts is structural: a window longer than a day takes minima across days on which *B*
itself differs, so it constrains a quantity the decomposition does not define. A reader who
rejects that reasoning should read the partition as spanning roughly
{{claim:field.f_sweep_lo}} to {{claim:field.f_form_roll48}} rather than as a point value.

The partition therefore has three separate sensitivities, and they are not interchangeable: which
year is anchored, the value of the one free parameter, and the form of the constraint window. An
earlier draft of this thesis attached the range of the first to the name of the third, which
understated the window sensitivity by leaving out its largest member. {{fig:partition}} draws the
three side by side on one scale so that the ranges cannot be exchanged again, with the widest
of them, the forty-eight hour window, visible as the one point that leaves the cluster.

{{fig:partition}}

### Interpreting the partition {#s-interpreting-partition}

This replaces an earlier estimate of about a quarter taken from source apportionment, and the
constraint refutes that value rather than refining it. Three statements about the new number have
to be kept apart, because the strongest reading is not supported.

**It is a constrained decomposition, not an observed apportionment.** The constraint rules out
decompositions that are physically incoherent, given that local sources emit continuously. It
does not measure how much material comes from where. Filter-based source apportionment
[@Hopke2016] at Kandy resolves soil, aged sea salt, vehicular, biomass-burning and industrial
factors [@Seneviratne2017], and none of those maps onto a two-way split. The defensible form of the claim
is that **under the stated background and minimum-increment assumptions, the constrained
decomposition assigns {{claim:partition.f}} of modelled concentration to the local increment.**

Local increment is not the same as locally emitted primary material. The model has no
chemistry, as {{ref:s-excluded-processes-known-limits}} states. Precursors emitted inside the basin can form particulate mass
inside it, and material formed outside can arrive already aged. The increment is defined by
spatial structure and timing rather than by origin, so it contains locally formed secondary
aerosol and excludes regionally formed aerosol regardless of where the precursors came from.
{{ref:s-independent-chemical-check}} supplies the one chemical check the thesis has, and it also refuted the simplest
reading, that the local increment can be treated as fresh primary aerosol.

The intervention statement therefore has to be weaker than the arithmetic suggests. It is not
established that removing every local source would remove half the concentration, because a
share of the increment is secondary material whose precursors are not all local and whose
formation would not stop with the emissions this decomposition can see.

Withdrawing the claim leaves a reader with nothing, so {{ref:s-independent-chemical-check}} replaces it with a bound. The
locally emitted primary share is constrained from both directions by the local share and the
secondary share together, with no further assumption, and at Kandy it lies between
**{{claim:chem.intervention_lo}} and {{claim:chem.intervention_hi}} per cent** of concentration.
The lower figure responds immediately to local emission control. The upper figure equals the
whole local increment and requires every locally formed secondary particle to vanish with it,
which is why the withdrawn claim sat at the top of a range and not in the middle of one.

That is the honest form of the statement, and it is more useful than either the withdrawn
version or silence: local action is worth substantially more than the retired quarter implied,
and its immediate effect is bounded well below half. A speciated measurement in the city is the
experiment that would narrow the range, and {{ref:s-measurement-would-settle-most}} lists it.
