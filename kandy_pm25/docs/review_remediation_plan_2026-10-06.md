# External review and remediation plan (2026-10-06)

An adversarial review of the codebase, written as an outside referee would, followed by the plan to answer
every finding. Registered results **stand as registered**; everything below is either a correction of an
error, a relabelling of what a registered quantity measures, or a new analysis declared **exploratory**
unless it is separately registered (Test C).

Status tags: `TODO` · `RUNNING` · `DONE (result)` · `USER` (needs the author's decision or action).

---

## 1. Findings

### Paper 1, the information-budget ladder

| id | finding | evidence | severity |
|---|---|---|---|
| R1 | **The rungs are not compared like for like.** Bud1/Bud2 use their stations only to fit an intercept and slope to Bud0 (a station's reading never enters that day's prediction); Bud3 uses the background stations' **same-day** reading. H4/H5 ("background > first two") therefore compare a calibration with a same-day observation. | `scripts/ladder_v2.py:105-109` vs `:110-118`; paper §2.3.3 states it, the abstract does not | major |
| R1a | Pilot probe (10 discovery cities, 5 splits, no shrinkage): first two as calibration **+4.1 %**; first two used same-day **+71.9 %**; background **+68.6 %**; background from two stations **+65.6 %**; background − same-day first two **−1.8**, first two win in 60 % of cities. | `scratchpad/review_sameday.py` (to be promoted, step L1) | pilot |
| R2 | H2 (stations 3–6 add +0.2) is close to guaranteed: a two-parameter affine map is already determined by two stations over hundreds of days. | as R1 | major (interpretation) |
| R3 | The prospective arm assumes the background keeps reporting in the scored half while the local stations have stopped. | `ladder_v2.py:111-118`, `run()` prospective block | moderate |
| R4 | Bud3 also uses more stations than Bud1 (all remaining pool stations vs two): count is confounded with type. | `ladder_v2.py:103-110` | moderate |
| R5 | Bud0 is leave-one-**city**-out: same-network neighbours (CNEMC, same country) on the same dates stay in training, probably flattering Bud0 and shrinking every gain above it. | `ladder_frames.py:145-157` | moderate |
| R6 | Scope: 4/72 confirmation cities tropical; median reference fraction 1.0. Kandy is tropical and low-cost only. | `confirm_REGISTERED_percity_reconstruction.csv` | moderate (framing) |
| R7 | The "background" is the 10th percentile of the same city's other monitors, not a regional series; only the 71 % recovery from a network 30–300 km away is regional, and it is exploratory. | paper §2.3.3, F.115 | moderate (framing) |

### Spatial learning curve (F.119 / F.123)

| id | finding | evidence | severity |
|---|---|---|---|
| S1 | **Bug: X5 (cLHS vs random) pools differences over all estimators**, including E0/E1, which do not depend on the sites chosen (differences exactly 0). Interval degenerates to [0.00, 0.00]. Per estimator, cLHS is slightly worse (−0.05 to 0.00). Verdict is also one-sided. | `spatial_curve_analysis.py:805-810`; both `summary.json` | major (bug) |
| S2 | Held-out set H = max(10, n//3): 14/23 full-frame cities score on 10 sites (Spearman SE ≈ 0.33); k=3 skill ≈ 0.10 for raster and kriging alike. | `spatial_curve_analysis.py:228-246`, `curve_q1_city.csv` | major (power) |
| S3 | No test that the between-city spread ("15/23 cross") exceeds sampling noise of a 10-site Spearman. | — | major (interpretation) |
| S4 | Crossover = first k whose bootstrap lower bound > 0, bootstrap over 100 **dependent** replicates of one city, up to 9 k × 2 estimators, no correction. | `:722-739`, `:780` | moderate |
| S5 | Reach is quantised to bin edges and pooled over k; sites merged only within 100 m, so 100–500 m neighbours straddle the split. | `:744-767`; `spatial_curve_freeze.py:51` | moderate |
| S6 | "Tropical inside the temperate envelope": min–max envelope already spans −0.02..0.50 at k=3; the 0.28 limit belongs to a test not run; 3/8 arm cities partly below. | results doc 2026-10-05 | moderate (interpretation) |
| S7 | Detection limit assumes per-unit SD 0.20; observed SD of per-city E3−E1 at k=3 ≈ 0.3. | `mde_for`, `:408-423` | moderate |
| S8 | Missing benchmark: a 1 km satellite PM2.5 product (GHAP / van Donkelaar) at the sites. | — | moderate (alternative) |
| S9 | Site mean over each site's own days, not shared days; "full record" is still the best 365-day window. | `spatial_curve_freeze.py:12-13,150` | minor |

### Kandy production model (Paper 2, thesis core)

| id | finding | evidence | severity |
|---|---|---|---|
| K1 | **Humidity correction is a constant** (`CLIM_RH_KANDY = 80`), so the Barkjohn RH term is a fixed offset; RH-driven over-reading follows the diurnal humidity cycle and is then imposed on T by the sharpening. | `src/stage1_satml/data/calibrate_fect.py:123,264` | major |
| K2 | **The coherence cap uses UTC days** (05:30–05:29 local), splitting the night; f is sensitive to the window form. | `scripts/build_additive_field_v2.py:163,222` | major (bug) |
| K3 | f is set by the cap (binding 49–75 % of hours): f ≈ 1 − mean(daily min T)/mean(T), a function of T's amplitude; the daily minimum of 24 noisy values is biased low. No noise analysis. "Resolved by physics" overstates it. | `build_additive_field_v2.py:223-226`, `kandy_f_reconciliation.py:90-95` | major (identification) |
| K4 | Shared inputs: FECT trains T, sets its conformal width and sharpens it; van Donkelaar sets the level and B; GHAP quasi-independent. Independent: NBRO (one pixel, instrument unknown), RF-CNN (+28 %), KOALA 2019. | `predict_T_anchor_v3.py`, `sharpen_T_diurnal.py` | moderate |
| K5 | W11 + one-sided coverage failure (25.7 % below, 1.9 % above) is evidence of an upward level bias, not an open question. | gotcha #75, F.65 | moderate |
| K6 | Intervals omit κ, f, emission proxy, calibration slope; background band hard-coded 0.70/1.25. | `build_additive_field.py:76`, `build_additive_field_v2.py:231` | moderate |
| K7 | GEMM applied to the all-age crude death rate over the whole 422 k domain (GEMM is ages 25+, age-specific); "300 avoidable" depends on f. | `src/stage1_satml/decomp/health_burden.py:45-50,102` | moderate |
| K8 | Sharpening assumes hour and month factors independent, pools a valley and a ridge sensor. | `sharpen_T_diurnal.py:58-63` | minor |
| K9 | Missing baseline: does the chain beat "just use GHAP / CAMS" at the independent Kandy records? | — | moderate (alternative) |

### Thesis

| id | finding | evidence |
|---|---|---|
| T1 | Chapters last built 2026-09-19; none carries F.117–F.123; `ch07_making_sure.md:51` still states the retracted deep-tropical reversal. | `#writing/thesis/chapters/` |

---

## 2. Plan

Order: what changes the paper's headline first, then bugs, then the Kandy chain, then documents.

### Phase L — the ladder (Paper 1)
- **L1** `DONE` Promote the probe to `scripts/ladder_v2_review.py` (exploratory; frozen modules imported, never edited).
  Same union frame, 21 splits, 5 learner seeds, cross-fitted weights, cluster bootstrap. Per city × split it
  re-computes the registered chain (parity check against `confirm_REGISTERED_percity_reconstruction.csv`) and adds
  symmetric arms, each fitted against stations 3–6 and shrunk toward Bud0 with a cross-fitted weight:
  `L2s` first two used same-day · `BGall` background from all remaining stations · `BG2` background from two
  remaining stations (count-matched). Both reconstruction and a **symmetric prospective** arm (all streams keep
  reporting; coefficients from the earlier half) — answers R1, R3, R4.
- **L2** `DONE` Same on the full-network frame (`mhgna` mirror), where more cities have ≥ 12 stations.
- **L3** `DONE` Leave-one-**network**-out Bud0 (clusters as in the bootstrap) on the union frame; report how much
  every rung's gain moves — answers R5.
- **L4** `DECIDED 2026-10-06: SKIP` (author). No fresh dense pool (20 CNEMC cities with ≥ 12 stations, 2 tropical);
  L1–L3 are reported as post-hoc re-analysis beside the registered result. Original wording: Decide on **Test C**: register the symmetric design (same-day use for every rung, count-matched)
  before scoring it on held-out data. Draft registration prepared by Claude; lodging is the author's call.
- **L5** `DONE` Paper 1 text (reference draft): Bud1 named a *calibration campaign* everywhere incl. the abstract;
  H2/H4/H5 interpreted under R1–R4; L1–L3 reported as exploratory; scope sentence (R6); background naming (R7).

### Phase S — spatial curve
- **S-a** `DONE` Recompute X5 per estimator (E3, E5, E10 separately), two-sided, both frames; declare the bug
  as an erratum in both results records and the ledger.
- **S-b** `DONE` Hierarchical re-analysis: Fisher-z of each city's rho at each k with its known sampling variance
  (n_held), city random effect; test whether between-city variance exceeds sampling noise (S3); replace the
  envelope rule by an estimated tropical − temperate difference with an interval (S6); empirical SD for the
  detection limit (S7).
- **S-c** `DONE` Crossover with a dependence-aware rule (site-level bootstrap, not replicate-level) and a
  Holm correction over k (S4).
- **S-d** `DOWNGRADED to text` Reach sensitivity with a 500 m merge radius and per-k bins (S5).
- **S-e** `DONE` Satellite 1 km PM2.5 benchmark at the sites (GHAP annual via GEE, van Donkelaar V6 from disk
  where covered), scored like E1 (S8).

### Phase K — Kandy model
- **K-a** `DONE` Local-day (Asia/Colombo) window in the coherence cap; recompute f (K2).
- **K-b** `DONE` Humidity: ERA5(-Land) hourly RH at each FECT site into Barkjohn; compare diurnal amplitude and f
  under constant vs hourly RH (K1).
- **K-c** `DONE` Bootstrap / noise model for the daily minimum of T → an interval for f that includes K-a, K-b
  and the window form (K3).
- **K-d** `USER (GBD download)` GEMM with ages 25+ and age-specific baseline rates (GBD Sri Lanka) (K7).
- **K-e** `DONE` Baseline: GHAP and CAMS at the NBRO and RF-CNN points vs the chain (K9, K5).
- **K-f** `USER` Rebuild the production chain only if K-a…K-d move a shipped number; the public webapp and
  release repo change only after the author approves.

### Phase D — documents
- **D1** `DONE` Ledger entry F.124 (this review) and errata on F.119/F.123 (X5) and F.43 (f wording).
- **D2** `DONE` `CONTEXT.md`, `CLAUDE.md`, `README.md` (public) brought in line.
- **D3** `DONE` Thesis: a claim-by-claim list of what each chapter must change (T1). The author rewrites the
  prose; Claude supplies the list and the numbers.

---

## 3. Log
(appended as each step completes; every result below is EXPLORATORY)

**2026-10-06 — S-a DONE (`scripts/spatial_curve_x5_erratum.py` → `{frame}/analysis/x5_erratum.json`).** Bug confirmed:
42–44 % of the pooled differences are exactly 0 and the registered interval is [0.00, 0.00]. Per estimator and per k
the intervals are real and narrow: E3 (kriging) cLHS − random, registered frame, k=3 +0.013 [−0.062, +0.061], k=5
−0.019 [−0.042, +0.028], k=8 −0.013 [−0.054, +0.002]; full frame k=3 0.000 [−0.049, +0.046], k=5 −0.024 [−0.042,
+0.024]. **X5's substance survives** (siting by design buys nothing resolvable, two-sided, at every k); the reported
numbers must be replaced and the bug declared as an erratum.

**2026-10-06 — S-b/S-c DONE (`scripts/spatial_curve_reanalysis.py` → `{frame}/analysis/reanalysis.json`).** Fisher-z
random-effects analysis of kriging − raster, sampling variance from the city's site count (optimistic):
- **S3, full frame:** between-city heterogeneity is **not significant** at any k (Q p = 0.06–0.26, I² 0.23–0.42); only
  **2 of 23** cities have an own interval excluding 0 (both positive). Registered frame: modest heterogeneity
  (p 0.01–0.02 at k 3–12, I² ≈ 0.45–0.5), again only 2/18 cities individually distinguishable. **"Cities split, 15/23
  cross" is not supported**: the per-city crossing labels are mostly within sampling noise.
- **S4 Holm crossover:** **3/23** cities (full) and **3/18** (registered) cross the raster, 2 of them at k = 3
  (registered rule: 15/23 and 11/18).
- **S6 tropical − other, k=3:** kriging − raster on the z scale **−0.22 [−0.45, +0.02]** (full, 7 vs 21 cities),
  −0.23 [−0.50, +0.02] (registered). Tropical cities gain *less* from kriging, if anything; "inside the temperate
  envelope" should become "no difference resolved; point estimate favours the raster in the tropics".
- **S7:** empirical SD of per-city paired differences at k=3 is 0.31 (full) / 0.37 (registered), not 0.20; the
  detection limit becomes **0.35** (full, 9 countries) / **0.51** (registered, 7) instead of 0.24 / 0.28.
- **S-d (reach, 500 m merge) — DOWNGRADED to text.** Sites 100–500 m apart are distinct sites, so including them in
  the near bins is legitimate; the defensible change is to state that "~1 km" is the resolution of the first bin.

**2026-10-06 — S-e DONE (`scripts/spatial_curve_satellite_benchmark.py` → `{frame}/analysis/satellite_benchmark.json`).**
GHAP annual 1 km at 1,506 sites (2022 used for windows after 2022 — declared). Median within-city rank skill: GHAP
+0.125 [−0.031, +0.297] vs built-up raster +0.097 (full); paired GHAP − raster +0.018 [−0.143, +0.170]; kriging at
k = 3/5/8 minus GHAP +0.012 / +0.002 / −0.017, all intervals spanning ±0.15. **Neither free product nor 3–8 stations
ranks neighbourhoods usefully (rho ≈ 0.1–0.15).**

**2026-10-06 — K-a/K-c DONE (`scripts/kandy_f_sensitivity.py` → `decomp/f_sensitivity.csv`).** Production B reproduced
exactly (max |diff| 0.0). Mean f over 2019–2023: UTC/min (production) **0.483**; local day/min 0.492; 2nd-lowest hour
0.455 (UTC) / 0.469 (local); 3-h running-mean min 0.456 / 0.468; 10th percentile 0.433 / 0.446. **f lies in ~0.43–0.49
across these choices** (plus 0.489–0.547 across window forms, F.108): the UTC-day issue is small (+0.009), the
extreme-value bias is real (−0.02 to −0.05). Quote f as "about 0.45–0.5, a bound under the cap", never "fixed by
physics".

**2026-10-06 — K-b DONE (`scripts/kandy_rh_sensitivity.py` → `decomp/rh_sensitivity.csv`).** ERA5 RH by local hour
07 89 % · 14 69 % · 19 87 % · 02 94 %. Barkjohn with hourly RH instead of 80 %: normalised 07 peak 1.337 → 1.287,
14 trough 0.736 → 0.811, peak/trough 1.82 → **1.62** (about 11 % less swing); the sensor-level f proxy is unchanged
(0.547 → 0.545). A full kappa-Koehler growth correction on top inverts the cycle (midday peak, night halved) —
implausible for a BLH-driven valley, so it over-corrects; **the diurnal shape cannot be pinned down without
co-location against a reference monitor (CEA)**. Action when the chain is next rebuilt: hourly-RH Barkjohn.

**2026-10-06 — K-e DONE (inline; GHAP monthly on disk).** NBRO Kandy: obs 19.6 / 22.7 (2021/22); GHAP at that pixel
17.6 / 18.8 (−10 % / −17 %); model 19.7 / 22.1 (+0.7 % / −2.6 %). The chain beats the off-the-shelf product at the one
reference-like record — one site, two years, instrument undocumented. The RF-CNN window (Nov 2022 – Feb 2024) is
outside GHAP's coverage except two months; not scored.

**K-d — BLOCKED on data.** Age-specific (25+) GEMM needs GBD 2021 Sri Lanka cause- and age-specific baseline
mortality, which is behind the GBD Results Tool login (`USER`: download "Sri Lanka, deaths, NCD + LRI, 5-year age
groups, 2019–2023, rate"). Until then the burden stays an illustrative appendix with this caveat.

**2026-10-06 — D3 DONE (`docs/thesis_change_list_2026-10-06.md`).** About 128 flagged items (ch07 46, ch00 and ch09 16
each). Most serious: (1) the thesis claims registry (`#writing` `claims.json`, 2026-09-23) still generates the ladder
numbers from files superseded by F.115/F.116, so 17.8, 40.6, 73 % and 4.2× print with the claims gate green; (2) the
retracted deep-tropical reversal runs through the abstract, ch01–03, §7.3 and ch09's Kandy recommendation; (3) the
registered confirmation and robustness tests are absent; (4) f "fixed by physics" in ch00/02/05/06; (5) the spatial curve
is still "underway" in ch10. Lines marked "PENDING L1" wait for the ladder re-analysis.
- **D4** `DONE` (new, from D3) Re-point the thesis claim generators and the ladder tables/figures (`T7_1`, `T7_2`,
  `T9_1`, `fig:ladder`, `fig:losses`, `fig:stationcount`, `fig:acquisition`) to the registered v2 result files, so the
  gate checks current numbers. Model work, no prose.

**2026-10-06 — D4 DONE (`scripts/build_claims.py`, new section `registered_v2`).** 111 new `v2.*` claim keys from the
registered v2 result files (confirmation H1–H5 and M1 both arms, rich Bud0 gain, learners vs HGB, full-network N1–N5)
and from this review (X5 per-k erratum, Holm crossover, empirical detection limits, tropical difference, GHAP benchmark,
f cap range, RH peak/trough; ladder re-analysis keys appear once L1–L3 finish). Old keys left in place so the current
thesis still builds; the change list maps old → new. Gate: **683 claims reproduce exactly**. Ladder tables/figures in
`#writing/src` still read the old files — they move when the author rewrites ch07/ch09.

**2026-10-06 — L1 DONE (`scripts/ladder_v2_review.py --frame registered --bud0 loco` →
`ladder_v2/review_registered_loco_*`).** Parity with ueyfr exact (72/72 cities, max |diff| 2.8e-14). Symmetric arms
(all fitted against stations 3–6, same-day use, cross-fitted shrinkage), cities with ≥ 8 pool stations:

| arm (median % daily RMSE gain over Bud0, cluster 95 %) | confirmation, n = 61 | union, n = 100 | union, prospective |
|---|---|---|---|
| first two, same-day (L2s) | +58.7 [43.7, 70.4] | +58.8 [44.9, 69.0] | +57.9 [45.5, 65.2] |
| background, registered construction (BGall) | +57.4 [44.1, 70.0] | +57.7 [46.4, 67.4] | +58.4 [42.8, 67.7] |
| background from two stations (BG2) | +57.4 [43.8, 68.1] | +57.2 [46.5, 65.9] | +57.0 [42.9, 65.1] |
| mean of two non-local stations (M2) | +60.2 [47.9, 69.1] | +59.0 [49.5, 67.6] | +58.2 [43.5, 66.6] |
| **background − first two (RMSE)** | **−0.15 [−0.82, +0.23]** | **−0.22 [−0.60, +0.04]** | +0.03 [−0.40, +1.00] |
| background − first two (exceedance) | −1.38 [−2.81, +0.23] | −0.11 [−2.49, +0.00] | 0.00 [−1.56, +0.95] |

Same cities under the registered (calibration-only) construction: first two +13.7, background +40.8, difference
+22.6. **Conclusion: the registered ordering (H4 +24.6, H5 +59.3) is produced entirely by how the stations are used,
not by what they measure.** Two same-day stations cut daily error by ~58 % whether they are "local", a "background"
quantile or any two other network stations; type and count beyond two make no resolvable difference (all paired
differences within ±1 point). Used only as a calibration, two stations give +8.5 % (H1). The robust finding is the
**value of same-day observation versus calibration**, roughly 58 % versus 9–14 %.

**2026-10-06 — L5 DONE (Paper 1 reference draft).** Abstract rewritten around same-day observation vs
calibration; new §2.3.6 (like-for-like methods), §2.7.9 (spatial re-analysis methods, GHAP caveat: it may have
been trained on these monitors), §3.1.8 (like-for-like results table), §3.6.5 (X5 erratum, heterogeneity, Holm,
tropical difference, detection limits, GHAP); §3.1 interpretation, §3.3, §3.4 note, §3.6.3/§3.6.4, §4.1, §4.2
advice, §4.3 (fourth correction), §4.4 (two new limitations), §4.5, §5, contributions 2/6/7, S3.1 (erratum
values), evidence map (new block + retired rows). Figure plan: new headline Fig. 3b (like for like), Figs 7/8
redrawn on the re-analysis, S4 (X5 erratum). §4.4 holds a placeholder for the L3 result.
- **F1** `DONE` Fig. 3b (`fig3b_like_for_like`) and Fig. 7b (`fig7b_spatial_noise`) built, viewed, captions in `CAPTIONS.md`; Figs 7/8 kept as the registered record with revised captions to come from the author.

**2026-10-06 — D2 DONE (partly).** `CONTEXT.md` (read-first block, f row, two retired rows), `CLAUDE.md` (new Current
State block, gotcha #104), public `README.md` (research section: rungs labelled by use, post-hoc correction paragraph,
spatial curve narrowed) and the Dehideniya report draft (flaw and correction, narrowed spatial results, new question
3) updated. Still to do at the end: release-repo ledger sync (F.124), commit and push.

**2026-10-06 — L2 DONE (`review_full_loco_*`, full-network mirror, 111 union cities).** Same-day: first two +54.4,
all-outer background +60.2, two-outer background +53.0, mean of two outer +54.9. Paired: all-outer − first two
**+2.48 [1.14, 3.72]** (exceedance +3.74 [1.42, 6.95]; prospective +2.37 [0.89, 4.11]); two-outer P10 − first two
−0.84 [−1.43, −0.29]; mean of two − first two +0.07 [−0.38, +0.22]. Registered construction, same cities: +10.7 /
+44.9 / +27.9. ⇒ no effect of station KIND; a small effect of COUNT (~10 vs 2 stations); ~90 % of the registered
ordering is use. Propagated to abstract, §3.1.8, §4.2, evidence map, F.124, CONTEXT, CLAUDE, README.

**2026-10-06 — L3 DONE (`review_registered_lono_*`, Bud0 leave-one-network-out).** Registered construction,
confirmation cities: first two **+13.3 %** (LOCO 8.5), background +42.5 (41.1), H4 +25.9 (24.6); union same cities
+20.3 / +41.4 / +22.5. Same-day: first two +63.0, background +59.1, background − first two **−0.21 [−0.55, +0.13]**,
exceedance 0.00 [−2.15, +0.25]. ⇒ LOCO flattered Bud0 modestly (registered first-station gain ~5 points
conservative); the like-for-like conclusion does not depend on it. §4.4 placeholder filled; F.124 updated.


## 4. Status at close of 2026-10-06
Done: L1–L3, L5, S-a–S-c, S-e, K-a–K-c, K-e, D1–D4, F1. Declined: L4 (Test C). Downgraded: S-d.
**Open, needs the author:**
- **K-d** GBD 2021 Sri Lanka age-specific baseline mortality (NCD + LRI, 5-year groups) for an age-25+ GEMM.
- **K-f** whether to rebuild the shipped Kandy chain with hourly-RH Barkjohn and a local-day cap. It moves the
  diurnal amplitude ~11 % and f by ≤ +0.01; the public webapp and release repo would change. Recommended: do it once
  the CEA reference data allow a co-located check, not before.
- **Thesis** rewrite from `thesis_change_list_2026-10-06.md` (the author's prose); the `v2.*` claim keys are ready.
- **Paper 1**: rewrite from the revised reference draft; Figs 3b/7b are the new headline visuals.

**2026-10-06 — decisions (author):** push both repos — DONE (framework `99d1513`, release `ddc0469`, verified 0/0 against
origin). **K-f: wait for the CEA data** before rebuilding the shipped Kandy chain (hourly-RH Barkjohn + local-day cap).
Next (model work): Paper 1 supplementary figures S1–S4 and a graphical abstract built on the corrected headline; thesis
table/figure generators re-pointed to the v2 result files.

**2026-10-06 — Paper 1 figures completed.** New same-day station-count curve (`ladder_v2_review_k.py`, 86 cities, full
networks): k = 1/2/3/5/8 read daily **+42.1 [31.8, 54.9] / +53.3 / +55.8 / +58.4 / +60.9 %**; second station +4.48
[2.51, 5.91]; recalibration ~11 % flat for every k. Built Fig. S1 (station count), S2 (reach — beyond ~1 km kriging
returns the city mean; within 0.5 km the median gain is ~0 too), S3 (X-T), S4 (X5 erratum) and a graphical abstract on
the corrected headline. Propagated to §3.2.1, §4.2, abstract, evidence map, F.124, claims (881 OK), captions, figure plan.
Next: thesis table/figure generators re-pointed to v2 (`#writing/src`).

**2026-10-06 — Thesis build repaired; v2 tables added.** (1) The thesis-A build had been FAILING since the 2026-09-23 C7
fix renamed claim keys (`order.*` → `order.{ghap,maiac}.*`, `stn3to8` → `stn3to6`): 12 stale tokens in
`#writing/pool/ch07_making_sure/{02,04}-*.md` re-pointed to the GHAP keys the old ones meant (values moved slightly with
the September fix). (2) `t_tables.py` T7_5 failed since the 2026-09-25 registry audit (it required held + refuted =
predictions); the check now allows not-tested and two-sided predictions, the table gains a column for them, and the note
reads 17 lodged / 14 run / 23 of 105 refuted. (3) New gated tables `T7_1_ladder_v2`, `T7_2_like_for_like_v2`,
`T9_1_next_v2` built from `v2.*` claims, beside the old ones. Build: claims 881 fresh, 99 sources, 43,014 words, 42
figures, 9 tables, abstract 339 words — assembles. ⚠ **Thesis A is assembled from `#writing/pool/`, not
`thesis/chapters/`**; the change list's line numbers refer to `thesis/chapters`, whose text the pool files carry.
