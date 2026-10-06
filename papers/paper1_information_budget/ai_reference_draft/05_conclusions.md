[STATUS: DRAFT — AI reference text; the author rewrites.]

# 5 Conclusions

We measured what each type of observation adds to a daily estimate of city PM2.5 that begins from
free global data. We did this under declared, code-checked information budgets, paired within city,
averaged over many random station splits, and confirmed once on 72 cities that were registered
before their data were retrieved.

In that population, which is mostly temperate and served by regulatory monitors, the first one or two
local stations reduce daily error by about 9 %. Further stations add a quarter of a point. A background
series adds about 40 %, more than the first local stations on ordinary days and far more for high days
and guideline exceedances, where the first stations add nothing detectable. No freely available
predictor, learner or siting design we tested improved the within-city ranking of stations over a
single built-up covariate by more than its test could detect.

These findings held under a richer starting estimate, under three other learners, including a deep
sequence model, and with each city's full station network; only the ordinary-day ranking softened when the
starting estimate was weak. For a map, cities split: in about two thirds, interpolation from a handful to a
few dozen stations overtakes a free land-cover layer, in the rest it never does, and one station informs
about a kilometre. Tropical networks, present once the curve was re-run on full records, behave like
temperate ones within what the data can resolve.

Whether the ranking changes in the tropics, where monitoring is scarcest, remains open. The public
record holds too few dense tropical networks to test it. A city there should treat local stations and a
background series as complementary, and the registered test should be repeated as tropical networks
grow.

The method may matter as much as the numbers. Two of our most striking exploratory results, a four-fold
advantage for local stations in the deep tropics and a monitor-trained covariate halving a station's
value, did not survive split-averaging and pairing. The confirmed first-station gain was less than half
the discovery estimate. Declared budgets, paired inference, averaging over random design choices, and a
single registered test on fresh data are what separated those results from the ones reported here.
