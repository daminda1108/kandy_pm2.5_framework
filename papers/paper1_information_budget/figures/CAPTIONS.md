[STATUS: DRAFT captions — AI reference text; the author rewrites. Each stands alone. Numbers match the figure,
which reads them from the result files; if a figure is rebuilt, re-check its caption.]

**Figure 1.** The declared information-budget ladder and the study design. (a) For each city and each random
split of its stations, Bud0 estimates daily PM2.5 from free global streams only (reanalysis weather, static
geography, satellite aerosol), using boosted trees trained with the city left out. Bud1 adds the first two
local stations, Bud2 stations three to six, and Bud3 a background series formed from the remaining stations.
Held-out stations, never used by any rung, score every rung. Gains are averaged over 21 splits and 5 learner
seeds before a two-level cluster bootstrap over cities. (b) The estimator was developed on the discovery cities,
frozen by hash, and tested once on registered confirmation cities; three registered robustness tests followed.

**Figure 2.** The two panels of cities. Triangles mark the 46 scored discovery cities and circles the 72
scored confirmation cities; crosses mark the 4 registered confirmation cities excluded by the keep rules.
Colour gives the climate band (numbers in the legend: discovery + confirmation), and open markers cities
whose networks are mainly low-cost sensors. Dashed lines mark the tropics (23.5°) and dotted lines 15°.

**Figure 3.** What each observation is worth on the confirmation panel. Registered endpoints H1 to H5 with
medians and two-level cluster 95 % intervals: reconstruction arm (filled, the registered estimate),
prospective arm (open, calibration on earlier days only) and the discovery panel (grey, exploratory). H1–H3
are % reductions in daily RMSE; H4 and H5 are differences in points of gain, background minus first two
stations, on the ordinary-day and exceedance losses. The grey band is H2's registered equivalence bound.

**Figure 4.** The confirmed verdicts under a richer sensorless baseline, three alternative learners and the
full station networks. Medians and cluster 95 % intervals on the confirmation panel; the dashed line in each
panel is the confirmed value. The full-network row scores 75 cities, three more than the others, because full
networks let three more cities pass the registered keep rules.

**Figure 5.** City by city: background minus the first two stations on ordinary days (a) and on guideline
exceedances (b). Each dot is one city, coloured by climate band, with the median and its cluster 95 % interval
below. On the confirmation panel the background leads on both losses. Among the discovery panel's
deep-tropical cities (exploratory) the ordinary-day difference leans toward local stations, but its interval
includes zero, while exceedances still favour the background.

**Figure 6.** One random split is one draw. The deep-tropical difference between the background and the first
two stations, as first reported from one station split and one learner seed (square), from 20 other splits
(circles; blue where the interval excludes zero), and averaged over 21 splits and 5 seeds (diamond). The
first-reported result sat near the edge of a wide distribution of possible estimates.

**Figure 7.** What additional stations buy for a within-city map. (a) Median within-city rank correlation
between predicted and observed station means against the number of fitting stations, on the registered
one-year records (solid) and on full station records (dashed); the numbers under each k give the cities
contributing in each frame. (b) For each primary city, the first k at which kriging or regression kriging
beats the free built-up raster, or "never" within the densities that exist.

**Figure 8.** Tropical cities against the temperate range, on full station records. Kriging curves of the
band-arm cities (|latitude| < 23.5°) over the envelope (grey) and median (dotted) of the 21 non-tropical
primary cities. One band-arm city (Guangdong) had too few stations to be scored at any k and is not shown.
At 8 cities in 7 countries the arm can resolve differences of about 0.28 in rank correlation.

**Figure 9.** Bounded spatial nulls. Paired within-city advantage over the single built-up benchmark for every
candidate tested, with median and 95 % interval; filled markers are registered tests, open markers
exploratory. The orange tick is the smallest effect each test could detect; no candidate's interval reaches
it. The embeddings' partial-correlation test (E3) is tested against zero on a different scale and is reported
in Table 3.5 instead.

## Fig. 3b — like for like (added 2026-10-06, F.124; post hoc)
**What a station is worth depends on whether its reading is used on the day.** (a) Median reduction in daily RMSE over
the free estimate, with two-level cluster 95 % intervals, on the 100 cities with at least eight pool stations. Grey:
the registered rungs on the same cities, where the first two stations only recalibrate the free estimate and the
background is read on the day. Coloured: every stream read on the day, each regressed with the free estimate against
stations three to six. (b) Paired within-city differences between the same-day arms, reconstruction (filled) and
prospective (open); the shaded band is ±1 point. Source: `ladder_v2/review_registered_loco_summary.json`.

## Fig. 7b — how much of the spatial curve is noise (added 2026-10-06, F.124; post hoc)
(a) Each primary city's kriging-minus-built-up-raster difference at three stations on the Fisher-z scale, with a 95 %
interval from its site count (optimistic). Between-city heterogeneity and the number of cities that cross the raster
after a Holm correction over densities are printed above. Tropical cities in orange. (b) Median within-city rank
correlation of the GHAP 1 km satellite PM2.5 surface and the built-up raster, and paired differences against kriging
at three, five and eight stations (two-level country bootstrap). GHAP may have been trained on these monitors, so its
value is an upper bound. Source: `spatial_curve_full/analysis/{reanalysis,satellite_benchmark}.json`.

## Fig. S1 — what k stations buy (2026-10-06, F.124; post hoc)
Median reduction in daily RMSE over the free estimate when the first k pool stations are read on the day (black) or
used only to recalibrate the free estimate (grey, the registered construction), 86 cities with full networks; the
fitting target is the last two pool stations, shrinkage weights are cross-fitted from other cities, and bands are
two-level cluster 95 % intervals. Source: `ladder_v2/review_k_full_summary.json`.

## Fig. S2 — reach by distance (2026-10-06)
Absolute error of the city-mean predictor minus that of kriging at held-out sites, by distance to the nearest fitting
station, at three and eight fitting stations; median over primary cities with the interquartile range across cities,
registered frame (left) and full records (right). Beyond about a kilometre kriging returns the city mean, so the
difference is exactly zero; within half a kilometre the median gain is also about zero. Source: `analysis/q3.parquet`.

## Fig. S3 — terrain as a moderator (X-T, exploratory)
Rank correlation across cities between four terrain descriptors and four outcomes of the spatial curve, with
two-level bootstrap 95 % intervals; registered frame (left, 18 cities) and full records (right, 23). None of the 32
intervals excludes zero. Source: `analysis/moderators_terrain.csv`.

## Fig. S4 — siting by design, corrected (erratum, F.124)
cLHS minus random siting in within-city rank correlation, per number of fitting stations, for kriging (black) and
regression kriging (orange), registered frame (filled) and full records (open), with the registered two-level
bootstrap. The registered summary's interval of [0.00, 0.00] came from pooling estimators that do not depend on the
sites chosen. Source: `analysis/x5_erratum.json`.

## Graphical abstract (2026-10-06)
Daily city PM2.5 error relative to an estimate from free global data, by how stations are used: as a calibration
campaign, or read daily (one, two, five stations). Sources: `review_k_full_summary.json`,
`review_registered_loco_summary.json`.
