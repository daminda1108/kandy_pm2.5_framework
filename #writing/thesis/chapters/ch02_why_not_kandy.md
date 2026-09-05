# Chapter 2. Why not Kandy, and what is at stake

Chapter 1 argued that most of the world's cities have an air quality field nobody can check.
This chapter makes that concrete for one city, and sets out what following from it would be
worth.

## 2.1 A city in a hole

Kandy sits on the floor of a steep valley in the central highlands of Sri Lanka, about 500
metres above sea level and roughly 100 kilometres inland from Colombo. {{dia:valley}} shows the
setting from the elevation model used throughout this work. The basin is closed to the south by
the Hantana range, which rises to more than 1,200 metres within a few kilometres of the city
centre, and it drains to the north-west along the Mahaweli valley. Relief across the modelled
domain is {{claim:kandy.relief_m}} metres over fifteen kilometres.

{{dia:valley}}

That geometry is the reason Kandy is a harder problem than a city of the same size on a plain,
and the difficulty has three parts.

**Concentrations vary over distances shorter than any global product resolves.** Terrain steers
flow, and the flow near a valley floor is not the flow a coarse driver reports. A model cell of
one kilometre may contain a busy junction, a river, a wooded slope and a residential terrace,
and the concentration at each will differ.

**The relationship between emission and concentration is mediated by a boundary layer that a
coarse model represents only in aggregate.** Nocturnal inversions and cold-air pooling can hold
a shallow polluted layer over a valley city for days at a time [@Whiteman2000; @Chemel2016]. The
same emission produces a very different concentration depending on whether the layer above it is
two hundred metres deep or two thousand.

**The monitors that exist are on the valley floor.** People live on the floor, so instruments are
sited there. A network in a basin therefore samples one horizon of a strongly stratified field,
and cannot constrain the rest of it. This is not a criticism of any particular network. It
follows from the same logic that put the city where it is.

## 2.2 What Kandy actually has

Two low-cost sensors, and no operating reference monitor.

The city had a reference-grade instrument at Torrington Park, which anchored the calibration of
published low-cost sensor records in the region. It is no longer in operation. The regulatory
authority operates a monitoring station with an hourly record extending back to 2019, but that
record is not publicly released and obtaining it requires a formal agreement.

So the working position for this thesis is a city of roughly four hundred thousand people, in
terrain that makes the physics harder than average, with two instruments of the class that
carries its own calibration problem [@Morawska2018], and no independent measurement against
which any of it can be checked.

{{dia:refbyband}}

That position is not unusual, and this is the point of the figure. Counting cities worldwide
that carry ten or more concurrent reference monitors, the deep tropical band has
{{claim:census.deep_tropical}} and the temperate band has {{claim:census.temperate}}, a factor
of {{claim:census.temperate_over_deep_tropical}}. The regime that most needs a method requiring
no local monitoring is the regime where local monitoring is scarcest. Any validation panel
assembled for this problem inherits that imbalance, and Chapter 7 reports every result
stratified because of it.

## 2.3 What is at stake

Two things, and they are different in kind.

**The first is health.** Fine particulate exposure is associated with cardiovascular and
respiratory mortality across a wide range of concentrations, with no threshold below which the
association disappears [@Burnett2018]. A district-level signal has been documented for Kandy in
hospital admission records [@Priyankara2021]. The annual mean concentration over the basin runs
{{claim:kandy.mean_min}} to {{claim:kandy.mean_max}} micrograms per cubic metre across the
anchored years, which is above the World Health Organization annual guideline throughout
[@WHO2021]. Chapter 7 gives the exposure and burden estimates that follow from the delivered
field, with their intervals.

**The second is that nothing can be prioritised without a field.** This is the more practical
stake and it receives less attention. A municipality deciding whether to reroute heavy vehicles,
restrict open burning, or relocate a bus terminus needs to know how much of the concentration at
a given place is generated locally and how much has arrived from outside the basin. Those two
components respond to entirely different interventions, and no single measurement at one point
separates them. A field that reports only a total is of limited use for a decision, however
accurate that total is.

The decomposition described in Chapter 6 exists for this reason. It separates a regional
background from a locally generated increment, and only the increment can be acted upon by a
local authority. For Kandy the decomposition assigns {{claim:partition.f}} of modelled concentration to the local
increment, so approximately half is attributed to a component generated inside the basin and
approximately half to material arriving from elsewhere. That number is derived in Chapter 6 from
a physical constraint rather than assumed.

Its consequence has to be stated carefully, and Section 6.6 states it in full. The figure makes
local action worth substantially more than the quarter this project previously assumed. It does
not license the arithmetic that eliminating every local source would remove half the
concentration, because the model contains no chemistry and part of the increment is material
formed in the atmosphere rather than emitted into it. The decomposition is a constrained split
rather than a measured source apportionment.

## 2.4 The question a ministry actually asks

The question in the literature is which model is most accurate. The question an environmental
authority in a city like Kandy asks is different, and it is the question this thesis is built
around.

**What would have to be bought to trust an answer here, and in what order?**

A reference monitor costs tens of thousands of dollars to install and requires trained staff and
consumables indefinitely. A pair of low-cost sensors costs a few hundred, at the price of a
calibration problem that then has to be solved. A rural background station costs about the same
as an urban one and serves no constituency, which makes it the hardest of the three to fund. A
mobile campaign costs staff time rather than capital, and produces a snapshot rather than a
record.

These are not interchangeable, and the literature provides remarkably little that would let an
authority rank them. The reason is structural rather than an oversight, and it is worth stating
carefully because it motivates the entire construction of Chapter 6. Answering the question
requires knowing what a model would produce **without** a given observation. For most model
families that is not a well-posed question: removing an input and refitting produces a different
model, so the difference between the two confounds the loss of information with the change of
model. The quantity an authority needs is not recoverable from the models the field currently
builds.

Chapter 6 describes a construction in which it is recoverable, and Chapter 7 reports the
measurement. The answer for Kandy is not the answer that the global average would give.
