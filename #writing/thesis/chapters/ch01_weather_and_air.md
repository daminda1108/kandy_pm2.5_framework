# Chapter 1. Why the weather is known and the air is not

A phone will report tomorrow morning's temperature in Kandy to within about a degree, the
chance of rain to within a few percentage points, and the wind to within a couple of metres per
second. The same phone, asked what the air will be like, either says nothing at all or reports a
single number for the whole country. This is not a difference in how much anyone cares. Air
quality is among the largest environmental contributors to death and illness worldwide
[@Burnett2018; @GBD2021Risk], and unlike the weather it can be acted upon: a road can be moved,
a fuel can be changed, a kiln can be closed. The asymmetry is a difference in what can be
measured, and it is worth setting out precisely, because everything this thesis does follows
from it.

## 1.1 Three conditions that weather forecasting satisfies

Modern weather forecasting works because three conditions hold at once, and it is unusual among
the environmental sciences in that respect.

The first condition is a **dense and global observing network**. Surface stations, radiosondes,
aircraft, buoys and satellites report continuously, and a forecast for anywhere on Earth is
constrained by observations taken within a few hundred kilometres of it in the preceding hours.
The network is not uniform, but there is no large populated region where the atmosphere goes
entirely unmeasured.

The second condition is that the **governing physics is closed**. The equations of motion for a
compressible fluid on a rotating sphere are known, they are not in dispute, and every term in
them is either resolved or represented by a parameterisation that can be tested against
observation. A forecast model can be wrong, and often is, but it is wrong in ways that can be
traced to a specific term.

The third condition is that **the observations can be assimilated into the physics**. Sixty
years of work on data assimilation has produced methods that combine a model state with new
observations in a statistically principled way, so that each new measurement corrects the model
and the correction propagates forward. This is the machinery that turns a network and a set of
equations into a forecast.

Remove any one of the three and forecasting in the modern sense becomes impossible. Air quality
removes all three.

## 1.2 Air quality satisfies none of them

**The observing network is thin and unevenly placed.** {{fig:obsdensity}} shows every location
worldwide that publishes fine particulate measurements openly. The pattern is the first thing to
notice about the field: measurement is concentrated in Europe, North America and eastern Asia,
and it thins towards the equator. The deficit is not random. It falls hardest on the regions
where concentrations are highest and where the population exposed per instrument is largest, so
the places with the most to learn from a measurement are the places least likely to have one.

{{fig:obsdensity}}

**The physics is not closed, because emission is a boundary condition that nobody measures.**
The atmosphere transports and removes particulate matter according to equations that are as well
understood as those governing the weather. What enters the atmosphere is a different matter. A
model of urban air quality needs to know how much material is emitted, from where, at what hour,
and of what composition, and none of that is observed directly. It is inferred from activity
statistics, fuel sales, traffic counts and emission factors, each of which carries an
uncertainty that is rarely quantified and is frequently larger than the quantity being
predicted. Chemistry compounds the difficulty: a substantial fraction of fine particulate mass
is not emitted at all but formed in the atmosphere from gaseous precursors, through reactions
whose rates depend on temperature, humidity, sunlight and the concentrations of other species.

**Assimilation is therefore of limited use.** Assimilating an observation corrects a model state,
but if the dominant error is in the emission field rather than in the state, the correction is
absorbed by the wrong term and decays as soon as the model is integrated forward. The technique
that made weather forecasting work does not transfer, because the error it is designed to
correct is not the error that dominates.

## 1.3 The consequence, stated plainly

For most of the world's cities, an air quality field is a model output that nobody can check.

This is a stronger statement than it appears. The literature on satellite and reanalysis fusion
products is large and technically accomplished [@vanDonkelaar2021; @Hammer2020; @Di2019;
@Wei2023], and those products report out-of-sample performance carefully. The difficulty is that
the out-of-sample test is almost always conducted where monitors exist, because that is the only
place a test can be conducted. A model trained where monitoring is dense and applied where it is
absent has been validated on one population and used on another. The transfer that matters, from
dense to sparse, is the one transfer that cannot be scored.

That is not an accusation of carelessness. It is a structural feature of the problem, and it
means that the usual response to doubt about a model, which is to test it more thoroughly, is
unavailable. Testing more thoroughly requires the observations whose absence created the doubt.

## 1.4 What this thesis does about it

The response taken here is not to build a better fusion product. It is to change the question.
Rather than asking how accurate a model is in a place where accuracy cannot be measured, this
thesis asks what a model is entitled to claim given the observations it actually has, and then
measures what each additional observation would be worth.

That reframing is what makes the problem tractable. The value of an observation can be measured
where observations are plentiful, by withholding them deliberately and scoring what is lost.
Provided the withholding is exact, so that the reduced model is the same model with less
information rather than a different model altogether, the measurement transfers to a city where
the observation was never available in the first place. Chapter 6 describes the construction
that makes withholding exact, and Chapter 7 reports what the measurement found.

The results are not what the field's intuition suggests. Freely available geographic data is
worth about as much as the first monitor a city buys. The second monitor through the eighth are
worth nothing that can be measured. The largest single gain comes from a rural background
station, which is the instrument that air quality programmes are least likely to fund because a
rural monitor serves no constituency. And the ordering of those recommendations reverses between
latitude bands, so the advice derived from the global average is the wrong advice for the
tropics, including for the city this thesis is about.

## 1.5 How the argument is arranged

Chapter 2 sets out why the problem is sharpest in a place like Kandy and what is at stake there.
Chapter 3 reviews what has actually been measured in the city over two decades and identifies
what none of those studies could establish. Chapter 4 describes the data and computational
resources available for the work.

Chapter 5 is an account of what was attempted and did not succeed. It is placed in the middle of
the thesis rather than in an appendix because the pattern in those failures turned out to be the
most useful thing the project learned. Chapter 6 sets out the model that did work, Chapter 7
describes how it was checked, and Chapter 8 establishes where it stops and why the stopping
point is a property of the question rather than a deficiency of the method. Chapter 9 sets out
what to build next, ranked by measured value. Chapter 10 documents the software and the
reproducibility machinery.

## 1.6 What is claimed and what is not

Stated here rather than left for a reader to extract.

This thesis does not claim a validated neighbourhood-scale map of Kandy. Chapter 8 shows that
such a map is not available at the resolution used, and explains why the limit is one of
definition rather than of data. It does not claim that the model captures atmospheric chemistry,
because the model contains none. It does not claim that the approach is validated for coastal
cities, because every city in the validation panel is a valley or a basin. And it does not claim
that machine learning solved the problem. The learning in this work is standard and the physics
is deliberately modest. What is new is the accounting: a declaration of what the model is
entitled to use, a guarantee that removing an entitlement degrades the model exactly, and a
measurement of what each entitlement is worth.
