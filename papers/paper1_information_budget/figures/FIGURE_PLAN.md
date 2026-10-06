# Figure plan — Paper 1 (rewritten 2026-10-05)

The first plan (2026-09) was written for the old single-split 48-city ladder. It included the `Bud4` tier, which
the paper no longer uses, and a "reversal" figure that the confirmation did not bear out. It is in git history.
This plan follows the current draft, section by section.

**Rules** (`papers/WORKFLOW.md`, gotchas #86/#94/#96):
- Every figure is built by `figures/build_figures.py` from the scored result files. No number is typed into a
  figure.
- Each figure is introduced in the text before it appears, and its caption stands alone.
- Intervals are the two-level cluster 95 % intervals used in the text.
- Every figure is viewed at print scale (6.02 in column) before it is called FINAL, and checked for colour-blind
  safety (`palette_cvd_check.py`).
- Style: `kandy_pm25/src/utils/plot_style.py`, STIX fonts, no em dashes in labels.

Status tags: `PLANNED` · `BUILT` (script runs, figure viewed) · `FINAL` (print-scale and CVD checked, caption agreed).

---

## Main figures

### Fig. 1 — The ladder and the study design (schematic) · BUILT 2026-10-05 (`fig1_design`)
- **Shows:** the four rungs, each with the streams it admits, the held-out stations that score every rung, and
  the discovery → freeze → registered confirmation → robustness tests sequence.
- **Data:** none; a concept diagram in the thesis flowchart style (`#writing/src/d_flowcharts.py`).
- **Introduced in:** §2.3.
- **Caption draft:** "The declared information-budget ladder and the study design. Bud0 uses only free global
  streams (reanalysis weather, static geography, satellite aerosol). Bud1 adds the first two local stations,
  Bud2 stations three to six, and Bud3 a background series from the remaining stations. Held-out stations, never
  seen by any rung, score every rung. The estimator was developed on 47 discovery cities, frozen, and tested
  once on 76 registered confirmation cities; three registered robustness tests followed."

### Fig. 2 — The two panels · BUILT 2026-10-05 (`fig2_panels`)
- **Shows:** a world map of the discovery (47) and confirmation (76 registered, 72 scored) cities. Marker shape
  shows the panel, colour the climate band, and fill whether the network is reference or low-cost.
- **Data:** `confirmation/confirmation_panel.csv`, `city_meta`, discovery frame. Natural Earth basemap
  (cache-only loader `thesisviz.natural_earth()`).
- **Introduced in:** §2.1.
- **Caption draft:** to write with the figure; it must state the band counts, read from the data.

### Fig. 3 — What each observation is worth: the confirmation · BUILT 2026-10-05 (`fig3_confirmation`)
- **Shows:** a forest plot of the five registered endpoints, H1 (first two stations), H2 (stations 3–6),
  H3 (background), H4 (background − first two) and H5 (the same on exceedance days), with cluster 95 %
  intervals.
  - Each endpoint carries three markers: confirmation, reconstruction arm (filled); confirmation, prospective
    arm (open); discovery (grey, exploratory).
  - H2's registered equivalence band [−1, +1] is shaded.
- **Data:** `ladder_v2/confirm_REGISTERED_summary.json`; discovery `ladder_v2/maiac_s21_b5_crossfit_c18_grid_dv2_summary.json`.
- **Introduced in:** §3.1.

### Fig. 4 — The verdicts survive the baseline, the learner and the station cap · BUILT 2026-10-05 (`fig4_robustness`); caption must state that the full-network row has n = 75
- **Shows:** Table 3.2 drawn as a forest plot, one panel per endpoint (H1–H5) and one row per variant: base,
  richer baseline, TabPFN, recurrent network, gradient boosting + ventilation, full networks.
  - The base row is drawn as a reference line in each panel.
- **Data:** `confirm_REGISTERED_summary.json`, `rich_REGISTERED_summary.json`, `learners_REGISTERED_summary.json`,
  `fullnet_full_summary.json`.
- **Introduced in:** §3.1.5–3.1.7.

### Fig. 5 — Ordinary days and exceedance days, city by city · BUILT 2026-10-05 (`fig5_city_by_city`)
- **Shows:** per-city paired difference, background minus first two, on the RMSE loss (left) and the exceedance
  loss (right), as an estimation plot. Each dot is one city, coloured by band, with the median and its cluster
  interval beside the dots.
  - The discovery deep-tropical cities are marked, where the ordinary-day sign flips while exceedances still
    favour the background (§3.3–3.4).
- **Data:** `confirm_REGISTERED_percity_reconstruction.csv`; discovery per-city file. **Needs** `dabest`, or a
  hand-built estimation plot, which avoids a new dependency.
- **Introduced in:** §3.3.

### Fig. 6 — One split is one draw · BUILT 2026-10-05 (`fig6_one_split`)
- **Built as one panel (2026-10-05):** the split draws only. The GHAP paired interval is not stored in any result file, so it stays in the text rather than being recomputed inside a figure.
- **Shows:** the two exploratory results that did not survive.
  - (a) The deep-tropical background − first-two estimate over 20 station splits. The one-split value (+33.3) is
    marked, the split-averaged value (−27.4) is shown, and the share of splits whose interval excludes zero
    (3 of 20) is printed from the data.
  - (b) The GHAP contamination, pooled (unpaired) against paired.
- **Data:** `verify_2026-09-25/honesty_seeds_maiac.csv`, `honesty_maiac.json` (F.115); the GHAP paired result
  (F.117 addendum).
- **Introduced in:** §3.5 and the Conclusions' methods point. This is the figure behind the paper's
  methodological lesson.

### Fig. 7 — What additional stations buy for the map · BUILT 2026-10-05 (`fig7_spatial_curve`)
- **Shows:** (a) pooled curves, the median within-city rank correlation against k, for E1, E2, E3, E5 and E10.
  The number of cities at each k is printed. The registered frame (18 cities) uses solid lines and the
  full-record frame (23 cities) dashed lines.
  (b) Per-city crossover: a strip of k× for each city, with "never" shown as its own column.
- **Data:** `spatial_curve{,_full}/analysis/curve_q1_pooled.csv`, `crossover_city.csv`.
- **Introduced in:** §3.6.1 and §3.6.3.

### Fig. 8 — Tropical cities against the temperate envelope · BUILT 2026-10-05 (`fig8_tropical_arm`)
- **Shows:** E3 curves of the 8 tropical band-arm cities (full records) drawn over the grey envelope of the 21
  non-tropical primary cities, with detection limit 0.28.
- **Data:** `spatial_curve_full/analysis/curve_q1_city.csv`, `F3_tropical_arm.json`.
- **Introduced in:** §3.6.3. This is the figure for the "a handful of stations, tropical cities included"
  reading.

### Fig. 9 — Bounded spatial nulls · BUILT 2026-10-05 (`fig9_spatial_nulls`)
- **Shows:** paired advantage over the built-up benchmark, with intervals and each test's own detection limit
  drawn as a band. Rows: learned pattern, embeddings E1/E2/E3, the six model families, and deliberate against
  convenience siting.
- **Data:** `phase2_learned_pattern.csv`, `embedding_spatial_test.json`, `spatial_tournament.json`,
  `siting_experiment_fixed.json`, `mde_recompute` output (F.105, F.111, F.103, F.115).
- **Introduced in:** §3.7.

## Checks done 2026-10-05
- All 9 main figures BUILT and viewed; layout fixed (legends, overlaps, label signs).
- Colour-blind check of every categorical palette (deuteranopia, protanopia, tritanopia simulation): minimum
  pairwise distance 0.105 (tritanopia, bands), 0.118 or more otherwise. Categories are always named in a legend.
- Draft captions in `CAPTIONS.md`. **Remaining before FINAL:** the author agrees the captions; the figures are
  checked at the target journal's column width.

## Changes required by the external review (2026-10-06, F.124)
- **Fig. 3, 4, 5** show the registered ordering (H4/H5). Keep them as the registered record, but every caption
  must say the rungs differ in use (calibration vs same-day), and the text must not read them as a ranking of
  observations.
- **New Fig. 3b — like for like.** A forest plot of the four same-day arms (first two, background as registered,
  background from two stations, mean of two outer stations) beside the registered first-two and background rungs,
  union cities (n = 100), with the paired differences. Data: `ladder_v2/review_registered_loco_summary.json` and
  `review_full_loco_summary.json`. This becomes the paper's headline figure.
- **Fig. 7 / Fig. 8** (spatial curve): drop the "cities split" strip and the min–max envelope; show per-density
  Fisher-z random-effects estimates with intervals, the Holm crossing count (3/23) and the GHAP benchmark line.
  Data: `spatial_curve{,_full}/analysis/{reanalysis,satellite_benchmark}.json`.
- **Supplementary S4** — X5 per estimator and k (erratum), from `x5_erratum.json`.

## Supplementary figures · BUILT 2026-10-06
- **Fig. S1** (`figS1_station_count`) — k = 1..8 stations read daily vs as recalibration (review, F.124). Replaces the
  planned recalibration-only station-count curve, which on its own would repeat the construction flaw.
- **Fig. S2** (`figS2_reach`) — kriging vs city-mean error by distance, both frames, primary cities.
- **Fig. S3** (`figS3_terrain_moderator`) — X-T, 16 correlations × 2 frames.
- **Fig. S4** (`figS4_x5_erratum`) — X5 per estimator and k (erratum).

## Dropped from the first plan
- **Bud4 tier:** not used in the paper.
- **Model-family tournament as its own figure:** folded into Fig. 9.
- **Kandy transect / change-of-support figure:** belongs to Paper 2.
- **"Average-day vs episode reversal" figure:** replaced by Fig. 5, which shows what the confirmation actually
  found.

## Graphical abstract · BUILT 2026-10-06 (`graphical_abstract`)
Bars of daily error reduction over free data: a calibration campaign (−11 %) against one, two and five stations read
daily (−42, −53, −58 %), with one line on station kind (local vs background, −0.2 points). Replaces the planned
four-rung staircase, whose ordering F.124 withdrew.

## Build order
1. Figs 3 and 4 (headline results, data ready).
2. Figs 7 and 8 (spatial curve).
3. Fig. 6.
4. Fig. 5.
5. Fig. 9.
6. Fig. 2.
7. Fig. 1.
8. Supplementary figures.
9. Graphical abstract.
