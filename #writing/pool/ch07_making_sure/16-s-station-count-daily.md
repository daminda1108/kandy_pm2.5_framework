## How many stations: read daily, or used as a calibration {#s-redundancy-begins}

The registered ladder adds two stations at its first ground rung, and that number was not chosen by
measurement. The budget specification sizes the stream to the deployed Kandy budget of two low-cost
sensors, which is a defensible choice for pricing the tier Kandy occupies and which leaves open how
the value of stations grows with their number. The sweep below adds stations one at a time, on cities
with their full networks, and scores each count in both of the uses that {{ref:s-like-for-like}}
separates [ledger F.124]. The curve itself is drawn in {{fig:stationdaily}} in the main text.

**Read on the day**, the curve is steep and then flattens. One station reduces daily error by
{{claim:v2.review.k.day1.median}} per cent [{{claim:v2.review.k.day1.lo}}, {{claim:v2.review.k.day1.hi}}],
two by {{claim:v2.review.k.day2.median}}, three by {{claim:v2.review.k.day3.median}}, five by
{{claim:v2.review.k.day5.median}} and eight by {{claim:v2.review.k.day8.median}} per cent. Paired within
city, the second station adds {{claim:v2.review.k.day_second_over_first.median}} points
[{{claim:v2.review.k.day_second_over_first.lo}}, {{claim:v2.review.k.day_second_over_first.hi}}] over
the first, and each station after the fifth adds very little.

**Used only as a recalibration**, the same stations give a flat line: about
{{claim:v2.review.k.cal1.median}} per cent for one station, {{claim:v2.review.k.cal2.median}} for two
and {{claim:v2.review.k.cal8.median}} for eight. A recalibration has two parameters, an intercept and a
slope, and one or two stations already determine them over hundreds of days. Further stations cannot
improve what is already determined, which is why the registered step from two to six stations is close
to zero by construction ({{ref:s-registered-confirmation}}).

The first version of the ladder reported that a single station captured essentially everything and
that a second added almost exactly nothing. That result came from shrinkage weights chosen on each
city's own held-out stations, which set the second station's weight to zero, and it described a
calibration. It is retired. Read daily, the second station is worth several points, and a daily
city-mean estimate saturates after a handful of stations rather than after one.

Three limits apply. The sweep prices stations for a **daily city mean** and says nothing about a map
of the city, which is the question of the spatial learning curve in {{ref:a-app-spatial}}. The stations
are those each network happens to operate, so what is priced is the marginal value of further
stations *as actually placed*; where a station is placed is a research question in its own right
[@Verghese2022; @Choi2026], and the deliberate-siting experiment of {{ref:a-app-spatial}} found no
detectable advantage of deliberate over convenience siting for the spatial pattern. And a second
station buys something the city-mean score does not see: the between-sensor comparison through which
low-cost sensors are checked against each other, which is how the reliability and calibration of the
Kandy sensors in {{ref:s-interval-calibration}} were obtained. A station also serves compliance,
public reporting and calibration, none of which this measurement addresses.
