# Pre-registration — do the 2020 lockdown and the 2021–22 fuel crisis constrain the local share?

**Written 2026-08-07, BEFORE any number was computed.**

---

## Motivation

The holiday instrument (F.22, F.23, F.29) established that Sri Lankan public holidays are a
usable natural experiment: they remove local activity while leaving transboundary transport
untouched, so the concentration drop measures the local contribution. It worked, it
corroborated the ~90% vehicular assumption, and it refuted one feature of the emission
clock.

Holidays are one-day shocks, so they bound the *daily* local share. Two much larger and
longer shocks sit unexploited in the same record:

1. **The COVID-19 lockdown**, roughly 2020-03-20 to 2020-05-11 in Sri Lanka — a near-total
   removal of discretionary traffic sustained for weeks.
2. **The fuel crisis**, roughly 2021-11 to 2022-09, peaking mid-2022 — severe and sustained
   fuel scarcity with queues, rationing and large reductions in vehicle-kilometres.

These are the only events in the record that plausibly change local emissions by a large
factor for long enough to be visible against seasonal variation. The shipped model already
*assumes* they matter — `FRAC_LOCAL_YEAR` is hand-lowered for 2020, 2021 and 2022 on exactly
this reasoning, described in the manuscript as "reasoned rather than fitted". **This test
asks whether the data support the reasoning**, which has never been checked.

---

## Design

Same estimator as F.22, which is the point: a method already validated on a different shock.
Each hour's observed concentration is differenced against the mean of its
(month × hour-of-day × ventilation-quintile) cell, so meteorology and season are controlled
non-parametrically and no seasonal contrast can be mistaken for an activity effect.
Ventilation comes from model drivers only.

Treatment periods are the two windows above. **Controls are the same calendar weeks in
non-shock years** (2019, 2023), so the comparison is within season by construction.
Ordinary working days only; holidays and Sundays excluded from both sides so the two
instruments cannot contaminate each other.

The effect is converted to an implied local fraction the same way as F.22, under an assumed
activity reduction, and reported as a **range across that assumption** rather than a point.

---

## Pre-registered predictions

**S1 — the lockdown effect is negative and larger than any holiday effect.** Sri Lanka's
lockdown removed more activity for longer than a single public holiday, so if the holiday
instrument measures what we claim, the lockdown must show a bigger drop than the −15.6% of
fixed public holidays. *Failure would undermine the holiday result retrospectively.*

**S2 — the fuel-crisis effect is negative and intermediate**, between the Sunday effect
(−7.8%) and the lockdown. Fuel scarcity suppressed traffic substantially but not totally,
and for months rather than weeks.

**S3 — ordering.** Sunday < fuel crisis < lockdown in magnitude. This monotonicity in
activity removed is the signature of a genuine local signal, and it is what made the holiday
result credible; the same structure should appear here.

**S4 — implied *f* is consistent with the converging estimates.** The implied local fraction
from the lockdown, at a 60–80% activity reduction, overlaps the interval already established
by four independent lines (coherence floor ≥0.41, network 0.446, hierarchical 0.392
[0.258, 0.525], holidays 0.24–0.52). *If it lands far outside, one of the two instruments is
wrong and this must be reported as a conflict rather than averaged away.*

**S5 — is the hand-set year variation justified?** `FRAC_LOCAL_YEAR` lowers *f* for 2020,
2021 and 2022. Report whether the measured shock effects support lowering it in those years
specifically. *No threshold; this is reported because the manuscript currently defends those
values by argument alone.*

---

## Falsifiers, stated plainly

If the lockdown shows **no** effect, or a positive one, then either the control design is
inadequate or the holiday instrument was measuring something other than local activity. In
that case S1–S4 are reported as failures and **the holiday-based line of evidence for *f*
must be downgraded**, not defended.

A specific known risk: 2020 also had anomalous regional conditions, and lockdowns across
India suppressed transboundary transport too. A drop at Kandy therefore does **not** cleanly
isolate local activity in the way a Poya day does. This is registered in advance as a reason
the lockdown estimate may be an **upper bound** on the local share, and it will be reported
as such regardless of the number.

---

## Prior

I expect S1 and S2 to hold and S3 to hold. I am least confident in S4, because of the
regional-confounding risk above, and I expect the lockdown-implied *f* to come out **too
high** for exactly that reason. If it does, that is evidence about the instrument, not about
Kandy.

**Artifacts:** `scripts/kandy_activity_shocks.py` →
`data/processed/decomp/kandy_activity_shocks.{csv,json}`.
