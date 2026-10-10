## The partition in detail {#s-partition-detail}

The non-negativity constraint and the production value of the local fraction are set out in
{{ref:s-partition-constraint-rather-than}}. This section gives what sets the number, its sensitivity to each
choice in the constraint, and how it should and should not be interpreted.

### What sets the number {#s-what-sets-partition}

The constraint binds on roughly half to three quarters of all hours, depending on the year. Where
it binds, the background on a given day equals that day's minimum hourly total, so the local
fraction is close to one minus the ratio of the mean daily minimum of *T* to the mean of *T*. The
fraction is therefore not an independent measurement of source shares. It is a function of the
diurnal amplitude of the anchor *T*: a deeper daily trough in *T* lowers the background and raises
the local fraction, and a flatter *T* does the opposite. Anything that changes the amplitude of *T*,
including the humidity correction applied to the sensor record that sharpens it
({{ref:s-excluded-processes-known-limits}}), moves the partition with it.

Two further properties follow from this. The minimum of twenty-four noisy hourly values is biased
low relative to the underlying daily floor, so a cap set on the single lowest hour places the
background too low and the local fraction too high. And because the day is a UTC day, the
minimum is taken over a window that does not match the local diurnal cycle.

### Sensitivity of the partition {#s-partition-sensitivity}

**The value of the free parameter matters little.** Sweeping *F*~min~ from zero to
{{claim:field.f_sweep_param_hi}}, four times the value used ({{claim:partition.f_min_parameter}}),
moves the fraction from {{claim:field.f_sweep_lo}} to {{claim:field.f_sweep_hi}}. The value used
was chosen as the smallest that removes the defect, before the resulting fraction was known.

**The form of the constraint window matters more.** The independent reimplementation of the
calendar-day form gives {{claim:field.f_form_calendar}}. Replacing it with a centred rolling
twenty-four hour minimum gives {{claim:field.f_form_roll24}}, and doubling that window to
forty-eight hours gives {{claim:field.f_form_roll48}}. The forty-eight hour form is reported rather
than excluded as an outlier. It drifts for a structural reason: a window longer than a day takes
minima across days on which *B* itself differs, so it constrains a quantity the decomposition does
not define.

The sweep and the window-form figures come from an independent reimplementation of the constraint
and not from the production code path. The reimplementation reads slightly higher than production
at every value of *F*~min~, by less than a hundredth, which is why its calendar-day value
({{claim:field.f_form_calendar}}) differs from the production value ({{claim:partition.f}}). The
production value is the one quoted as the headline, because a separate check rebuilt the
production background exactly from the stored inputs; the reimplementation is quoted only for the
window forms, which the production sweep does not cover.

**The day boundary and the daily-minimum statistic matter most among the in-day choices.** A
sensitivity analysis on the production path varied both. Taking the day in local time rather than
UTC raises the fraction by about a hundredth. Replacing the single lowest hour by a less extreme
statistic (the second-lowest hour, the minimum of a three-hour running mean, or the tenth
percentile of the day) lowers it by two to five hundredths, which is the size of the low bias of the
single-hour minimum. Across these eight combinations of day boundary and statistic the mean local
fraction over the anchored years runs from **{{claim:v2.f.cap_min}} to {{claim:v2.f.cap_max}}**.

The partition therefore has four separate sensitivities, and they are not interchangeable: which
year is anchored ({{claim:partition.f_lo}} to {{claim:partition.f_hi}}), the value of the free
parameter ({{claim:field.f_sweep_lo}} to {{claim:field.f_sweep_hi}}), the form of the constraint
window ({{claim:field.f_form_calendar}} to {{claim:field.f_form_roll48}}), and the day boundary and
daily-minimum statistic ({{claim:v2.f.cap_min}} to {{claim:v2.f.cap_max}}). An earlier draft of
this thesis attached the range of the first to the name of the third, which understated the
window sensitivity by leaving out its largest member. {{fig:partition}} draws the first three side
by side on one scale; the fourth was computed after the figure was built and is given here in
the text.

{{fig:partition}}

The defensible statement is that **under the non-negativity constraint the local fraction lies between about
{{claim:v2.f.cap_min}} and {{claim:v2.f.cap_max}}**, with {{claim:partition.f}} as the production
value. It is a bound set by the
constraint and by the diurnal amplitude of the anchor, not a value that physics has fixed. A reader
who rejects the reasoning against windows longer than a day should read the upper end as
{{claim:field.f_form_roll48}}.

### Interpreting the partition {#s-interpreting-partition}

This replaces an earlier estimate of about a quarter taken from source apportionment, and the
constraint refutes that value rather than refining it: every choice examined above places the
fraction well above a quarter. Three statements about the new number have to be kept apart,
because the strongest reading is not supported.

**It is a constrained decomposition, not an observed apportionment.** The constraint rules out
decompositions that are physically incoherent, given that local sources emit continuously. It
does not measure how much material comes from where. Filter-based source apportionment
[@Hopke2016] at Kandy resolves soil, aged sea salt, vehicular, biomass-burning and industrial
factors [@Seneviratne2017], and none of those maps onto a two-way split. The defensible form of the claim
is that **under the stated background and minimum-increment assumptions, the constrained
decomposition assigns about {{claim:partition.f}} of modelled concentration to the local
increment, within {{claim:v2.f.cap_min}} to {{claim:v2.f.cap_max}} across the choices of day and
statistic.**

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
whole local increment, so it moves with the local fraction: across the day-boundary and statistic
choices above it would sit at the corresponding local fraction, between {{claim:v2.f.cap_min}}
and {{claim:v2.f.cap_max}} of concentration. It requires every locally formed
secondary particle to vanish with the local emissions, which is why the withdrawn claim sat at the
top of a range and not in the middle of one.

That is the honest form of the statement, and it is more useful than either the withdrawn
version or silence: local action is worth substantially more than the retired quarter implied,
and its immediate effect is bounded below half. A speciated measurement in the city is the
experiment that would narrow the range, and {{ref:s-measurement-would-settle-most}} lists it.
