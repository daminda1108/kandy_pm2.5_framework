# Verification and re-run programme — 2026-09-25

**User directive (2026-09-25):** re-run everything that feeds a claim so that every finding and
test is right, honest and accurate before numbers are locked into Paper 1. Run it while the
spatial learning curve's E8/E9 wave 2 finishes.

**Rules for every item**
1. Back up the old output to `data/processed/modular/_backup_pre_verify_2026-09-25/` before re-running.
2. Fix the defect **inside the script that produces the output** (gotcha #70), never by patching a CSV.
3. After re-running, write an old-vs-new diff for every quoted number to `modular/verify_2026-09-25/`.
4. Every A-vs-B effect is paired within city, with a city bootstrap **and** a cluster bootstrap (gotcha #91, F.104).
5. A changed number goes to the ledger (new F-entry), `CONTEXT.md`, `claims.json`, then the draft. The old
   thesis is **not** corrected (user, 2026-09-23).
6. A result that weakens is reported as it is. Nothing is re-specified to rescue a finding. Any analysis
   choice made after seeing the new numbers is labelled post hoc.

## A. Defects that change data flowing into results (re-score required)

| # | defect | affected outputs | fix | acceptance check |
|---|---|---|---|---|
| A1 | **CNEMC cities carry no band and are classed LCS.** Band and class come from `openaq_manifest.csv`, which holds OpenAQ cities only; `NaN >= 0.5` is False. | every band-stratified and instrument-class result: F.52, F.92, F.96, F.97, F.102, F.107, F.109, F.112, F.113, F.114 | `src/modular/city_meta.py` (`attach_meta`, refuses a missing band) wired into every ladder script | 47 cities: 13/13/11/10; CNEMC = reference; deep-tropical numbers bit-identical (no CNEMC city is deep-tropical) |
| A2 | City 3147 is still in `revalidate_ladder.py` (GHAP) and `station_count_curve.py` | `ladder_revalidated.csv`, F.102 | `restrict_to_stream_complete` + `validate_bud0_frame` | 3147 absent; diff reported |
| A3 | Orderings (LOB) are scored on GHAP only; the headline stream is MAIAC | F.97 ordering | run the ordering variants on both streams | MAIAC ordering reported beside GHAP |
| A4 | The LOB output labels the step "three to eight"; the code takes `pool[:6]` | F.97 labels | relabel from the slice the code takes (gotcha #92) | the label is generated from the slice |
| A5 | `except Exception: r = None` in `ladder()` loops drops a city silently | all ladder outputs | count and name every dropped city; refuse if any drop is unexplained | the drop log is empty, or every entry is explained |
| A6 | No hours-per-day completeness rule for a city-day | the frame | sensitivity: require ≥ 18 h per station-day; re-score the headline ladder | headline paired effects move < CI half-width, or the rule is adopted |

## B. Design choices that must be disclosed, and tested where cheap

| # | issue | test | outcome use |
|---|---|---|---|
| B1 | STATIC_GEO is averaged over monitoring sites, which include the held-out stations | recompute over non-held-out sites only; re-score Bud0b/Bud0c | if the ladder moves materially, adopt; else disclose with the number |
| B2 | Bud1/Bud2 affine coefficients are fitted over the scored period | temporal split: fit on the first half, score on the second | report both; the split version is the honest calibration value |
| B3 | The shrinkage weight w is selected on the scored days | nested: choose w on the first half, score on the second | same |
| B4 | The Bud3 background is a within-network proxy (1–2 stations) | already tested by F.54 re-run (73 % recovery); re-run on the corrected frame | disclosure + number |

## C. Statistical and registry corrections

| # | item | fix |
|---|---|---|
| C1 | δ = 0.130 (spatial detection limit) was derived on 46 cities, reused on 47 | recompute δ on the 47-city frame |
| C2 | Phase 2 learned pattern (2jyfg) lacks a bootstrap interval | add a city bootstrap |
| C3 | 2jyfg deviations (best-of-3 learners vs MLP-first; static-only inputs) | re-run the registered MLP-first spec; report both |
| C4 | `registrations.json`: bkpyr missing C1; z89kt P4 still "held"; amendment 3 not listed | correct the registry; P4 → not supported (paired) |
| C5 | Spatial curve X6: ranking clause not implemented | implement before the summary run |
| C6 | D-7 count conflict (22 vs 23 merged pairs) | recount from the freeze; correct the docs |
| C7 | `spatial_curve_dl_tabpfn.py` header still describes a GPU scorer | fix the text |
| C8 | Cluster-bootstrap verdict flags only the lower bound | flag two-sided (excludes zero either way) |
| C9 | F.104 widening range quoted as "1.45 to 1.97" | recompute from the outputs; quote the verified range |
| C10 | `CONTEXT.md` "17.02 [4.57, …]" typo (the ledger says [4.98, 21.83]) | fix |

## D. Order of execution

1. A1 + A2 + A4 + A5 (code only), then re-run the ladder family in one pass:
   `revalidate_ladder` → `ladder_maiac` → `ladder_order_and_bootstrap` (A3) → `loss_sensitivity` →
   `precip_ladder_test` → `station_count_curve` → `independent_background_revalidated` → the F.114 paired checks.
2. Diff everything against the backup, then write the ledger entry (F.115).
3. B1–B3 sensitivity runs; A6.
4. C1–C3 (spatial tests), C4–C10.
5. Regenerate `claims.json`; update `CONTEXT.md`; then resume the Paper 1 draft with locked numbers.

## Status log
- 2026-09-25: plan written. A1 diagnosed and `city_meta.py` built and checked (57 cities in metadata; 47 scored:
  13/13/11/10; 32 resampling clusters in the metadata, fewer among the scored cities).
- 2026-09-25: **A7 added.** `ladder()` scores each city on ONE station split (one fixed seed decides the
  held-out set and the pool order). No result yet measures split-to-split variation. Test: re-run the
  headline ladder over 20 split seeds and report the distribution of each paired effect.
- 2026-09-25: **B3 sharpened.** `shrinkage.optimal_weight` takes the median of the minimisers on the
  five 80 % training parts and scores on ALL days; no fold is evaluated out of sample. Its docstring
  ("select w by cross-validation") and draft §2.3.4 ("held-out error") are inaccurate. Describe it as
  an in-sample, bagged estimate of one scalar; quantify the optimism under B3.
- 2026-09-25: `DropLog` (`src/modular/runlog.py`) added; wired into `revalidate_ladder.py` together with
  `restrict_to_stream_complete`, `validate_bud0_frame` and `attach_meta` (A1, A2, A5).
- 2026-09-25: **A2 done for the GHAP ladder** (`revalidate_ladder.py`, 47 cities, 0 drops). Pooled Bud0c
  steps: first two stations 17.85 → **14.95 %**, stations 3–6 0.10 → 0.13 %, background 40.56 → **38.44 %**.
  Bands now 13 / 13 / 11 / 10; classes 31 reference / 16 LCS (were 20 / 27).
- 2026-09-25: **A8 added — panel-composition instability.** Removing ONE training city (3147) moved other
  cities' Bud0b/Bud0c RMSE by an IQR of about ±5 % and up to +50 % (city 1504 Bud0c 31.6 → 41.6). The
  60 static features take one value per city, so a 46-city training set lets the learner approach city
  identity. Test: leave-k-cities-out perturbations (k = 1, 3; 20 draws) → spread of each headline paired
  effect. Also note HGB turns on early stopping above 10,000 rows (a random 10 % validation split set by
  `random_state`); check the learner-seed sensitivity at the same time.
- 2026-09-25: `scripts/ladder_frames.py` = the ONE frame builder (`build_bud0_frame(stream)`, `fit_loco`).
  Verified: reproduces `ladder_maiac.build_maiac_frame()` exactly (30,303 × 77, `assert_frame_equal`).
- 2026-09-25: `independent_background_revalidated.py` also (a) keeps 3147, (b) runs on GHAP only, and
  (c) reports recovery as a **ratio of medians** (`indep.median / own.median`), which is forbidden;
  it becomes the median of the within-city ratio plus the paired difference, with a bootstrap.
- 2026-09-25: **Early stopping is ON** in every Bud0 fit (sklearn 1.8, `early_stopping="auto"` above
  10,000 rows; training sets are ~29,000). "300 iterations" is a cap; a random 10 % of TRAINING rows (not
  city-grouped) is held aside and the stop point depends on `random_state`. No target leakage (the target
  city is never in training), but the draft said "300 iterations"; corrected. A8 covers seed sensitivity.
- 2026-09-25: **Order test re-run on both streams** (`ladder_order_and_bootstrap.py`, 0 errors).
  MAIAC: background after stations 3–6 **37.07 %**, before **33.12 %**; stations 3–6 **0.12 %** without a
  background, **2.07 %** with one (~17×). GHAP: 38.44 / 37.61; 0.23 / 2.97 (~13×). "More than twenty
  times" was wrong on both streams. Order-robust conclusion stands (these are descriptive medians).
- 2026-09-25: `precip_ladder_test.py` never COMPUTED verdicts for P3 or P4 (numbers printed, verdicts typed
  by hand). Now computed: P3 = paired interval of the stations 3–6 gain contains zero (the registration
  gives no threshold, so none is invented); P4 = paired background-minus-first-two, interval above zero.
  GHAP = registered primary; MAIAC = labelled robustness. `loss_sensitivity.py`'s "background largest"
  printout was unpaired; replaced by a paired pooled comparison per loss.
- 2026-09-25: `station_count_curve.py` docstring claimed parity with `ladder()`; in fact every k is shrunk
  toward Bud0, so k = 2 equals Bud1 exactly and k = 6 only approximates Bud2. Docstring corrected.
- 2026-09-25: `scripts/ladder_honesty_checks.py` written (A7, B2, B3): variants prod / prod_T / temporal /
  no_shrink / loco_w with a parity assertion against `ladder()`, plus 20 split seeds.
- 2026-09-25: **station count re-run (MAIAC, headline).** One station **23.4 % [8.96, 38.88]** (n = 46; old GHAP 17.02 [4.57, 21.83] — the CONTEXT '4.57' was this old bound, not a typo). Second station adds **+0.09 [−0.01, +0.35]** paired; saturation at one holds. Max extra over one +0.37 [0.09, 1.04] at k = 4. city143 (Chengdu) has no k = 1 point: its first pool station overlaps < 30 days; the step is skipped silently (A6).
- 2026-09-25: **C6 resolved.** D-7 recounted from the files: 47 merged pairs, **23** < 30 common days (5 none), 24 scored in 9 cities. Amendment 2 (lodged) says 22 twice; CLAUDE.md said 22 of 46. Correction note appended to the local amendment copy; CLAUDE.md fixed; paper discloses. Result unchanged (0.080 vs 0.699). **C7 done**: `spatial_curve_dl_tabpfn.py` header rewritten (CPU-only, D-8, the cross-machine caveat, tabpfn 8.5.0 pin).
- 2026-09-25: **C4 — registry audit** (`verify_2026-09-25/registry_audit.md`, spot-checked by hand on
  bkpyr C1 (F.95: P1 held, P2 held, P3 refuted, P4 refuted, P5 held) and nxqgb (F.78: all three priors
  refuted)). The registry UNDERCOUNTS: 38 predictions recorded vs **48** registered across the seven run
  registrations. bkpyr omits C1 (5) and R3 (3, never testable, F.94); g6hqb omits the two Colombo re-run
  priors; nxqgb counted gate passes as "held" (priors: 0 held / 3 refuted / 1 unscored); z89kt P4 not
  supported paired (F.113); amendment 3 (79qkw) absent. Audited totals before today's re-runs: 48 / 26
  held / 18 refuted / 4 not tested. ⚠ g6hqb's "Bud0c→Bud1 5–15 %" prior flips to held at 14.95 % on the
  corrected frame (a margin of 0.05 points; report it as narrow). "11 registrations, 13 of 38 refuted"
  is RETIRED. Registry to be rewritten after the z89kt re-run.
- 2026-09-25: **z89kt re-run (GHAP, registered primary)** — numbers bit-identical to 2026-09-23 (the shared
  builder reproduces that frame). 36 of 47 cities pass the 90 % coverage gate (all 11 CNEMC excluded: no
  ERA5-Land precipitation); 35 scored (1677 has no outer ring). Verdicts now COMPUTED:
  P1 refuted (−1.04 [−5.50, +4.33]); P2 refuted (−0.30 [−2.12, +3.23]); **P3 not adjudicable** — the
  registration says "bounded near zero" with no bound; the stations 3–6 gain with precipitation is +1.12
  [+0.09, +1.46] (3.5 % of the first-two gain), interval excludes zero, so a strict reading fails and a
  loose one holds; a verdict chosen after seeing the data would be post hoc; **P4 not supported**
  (+0.02 [−12.63, +7.15], 18/35); P5 held in direction (+16.4 [+4.1, +50.6] → +8.6 [−3.8, +34.6]; with
  precipitation the deep-tropical interval spans zero on this 35-city GHAP frame).
  **z89kt: 5 predictions, 1 held, 3 refuted, 1 not adjudicable** (F.112 recorded 3 held / 2 refuted).
  TODO at the end: re-run `precip_ladder_test.py --stream ghap` so its JSON carries the P3 wording.
- 2026-09-25: **C9 done — cluster bootstrap re-run on the corrected ladders** (`cluster_bootstrap.py`; its
  merge had to move to `city_meta` because the ladder outputs now carry `src`). 47 cities in **28** clusters
  (not 29: 3147 was South Africa's only city); 22 singletons; CNEMC 11. Widening, pooled steps:
  GHAP 1.27 / 1.15 / 1.45, MAIAC 1.33 / 2.21 / 2.14 → **1.15–2.21×** (retire "1.45–1.97"). MAIAC background
  cluster interval [19.18, 43.59]. Deep-tropical inversion, MAIAC: **+33.34 [+7.00, +50.07]** under both
  bootstraps (13 cities, 12 clusters); GHAP +2.29 [−9.61, +38.11], undetectable.
- 2026-09-25: `colombo_zeroshot_bud0c.py` and `learner_sensitivity_bud0c.py` dropped every row with any
  missing geography value (removing the censored city 2168 as well as 3147); both moved to the shared
  builder. The learner test now also reports the paired effects per learner, and handles MAIAC's missing
  days (imputer + missing indicator for Ridge only). Queued.
- 2026-09-25: **z89kt MAIAC robustness (exploratory):** P1 refuted; P3 +0.11 [0.00, +0.53]; P4 −6.90
  [−23.10, +2.01] (13/35), not supported. ⚠ **Panel-composition signal:** the deep-tropical inversion on this
  frame reads +35.6 [−6.5, +55.2] (n = 13) against +33.3 [+7.0, +50.1] on the full MAIAC ladder for the SAME
  13 cities. The only difference is the TRAINING set (the precipitation gate removes the 11 CNEMC cities from
  the Bud0c fit). The inversion's lower bound therefore depends on which cities train the sensorless rung;
  A8 must report this, and the headline should carry it.
- 2026-09-25: **C1 + C2 done** (`scripts/mde_recompute.py`, the identical simulation imported from
  `phase1_frame_and_power.mde`). Test-specific 80 % detection limits: 2jyfg Phase 2 **0.130** (sd 0.279, n 46;
  the reused value is right here); 6udm3 E1 **0.180** (sd 0.421) and E2 **0.080** (sd 0.174); F.105 families
  0.09 (stepwise LUR) to 0.16 (gradient boosting), random forest 0.15. The single "0.130" overstated the
  power of E1, RF and GB and understated E2. No result is near its bar, so every null stands; each test must
  carry its OWN limit. **C2:** Phase 2 learned minus baseline **+0.022 [−0.062, +0.050]**, 25/46 cities.
- 2026-09-25: **Independent background re-run (MAIAC, 3147 excluded, paired).** 20/47 cities have a donor
  30–300 km away (26 none in range, 1 no overlap). Per-city recovery **71 % [44, 82]** (n = 19 with own
  gain > 1 pp); paired independent − own **−13.8 pp [−20.6, −7.8]**; nearer half (62 km) 83 % [53, 94],
  farther half (152 km) 45 % [37, 76]. The old "73 %" was median(indep)/median(own); retired. Only 4
  deep-tropical cities have a donor: no band-level number is quotable.
- 2026-09-25: independent background on GHAP (continuity with F.54): per-city recovery 73 % [56, 84], paired −12.4 pp [−19.1, −6.9]; near 84 % [70, 94], far 56 % [38, 80]. Consistent with MAIAC; conclusion stream-robust.

## ⚠ HEADLINE STATUS after B1/B2/B3/A7 (2026-09-25) — the deep-tropical inversion is DIRECTIONAL, not established

MAIAC stream (the headline), paired bg − first2 in the deep tropics (negative = local stations win):
| check | median | 95 % interval |
|---|---|---|
| production split (F.96/F.97c quote this) | −33.3 | [−50.1, −7.0] |
| same, scored on later half only | −26.8 | [−44.1, −14.8] |
| coefficients + w fitted on earlier half, scored on later half | −24.9 | [−42.3, +1.3] |
| no shrinkage (w = 1, no use of held-out stations) | −33.7 | [−55.0, +20.0] |
| w borrowed from other cities (deployable) | −28.4 | [−51.3, +20.3] |
| static geography from non-held stations only (B1) | −24.2 | [−60.4, +4.4] |
| 20 station splits (A7) | median −22.6, range −36.4 … −4.6 | interval excludes 0 in **3 / 20** |
| training without the 11 CNEMC cities (precip frame, 35 cities) | −35.6 | [−55.2, +6.5] |
Direction: local stations ahead in **20/20 splits and every variant**. Significance: in a minority.
**Verdict: the inversion is directionally consistent and of plausible size (~20–35 points), but its
statistical support depends on the station split, the shrinkage choice and the training panel. F.96's
"robust" and the "4.2×" ratio are retired; quote the direction, the split distribution and the variants.**

What IS robust on MAIAC across all 20 splits: first two stations 18.8 % (13.7–25.8), interval > 0 in 20/20;
background 29.7 % (21.0–36.0), 20/20; stations 3–6 ~0.07 %; pooled bg − first2 −1.7 (−8.4 … +4.9), never
excludes 0 (no pooled ordering). GHAP (10 splits): pooled bg − first2 +11.7 (+8.4 … +14.1), excludes 0 in
6/10; DT ≈ 0. The production split gives first2 23.6 on MAIAC, near the top of the split range: every
headline should be the split-averaged estimate (next: `split_averaged_ladder.py`).
B1: non-held static geography changes Bud0c RMSE by a median +2.0 % (IQR −9.7 … +12.2); first2 23.6 → 17.1.
- 2026-09-25: **A6 (completeness ≥ 18 h per station-day, equal weight per station).** Frame 30,303 → 28,893
  city-days; 45 cities scored. first2 23.57 → 18.16; bg 37.07 → 41.17; **pooled bg − first2 +2.25 → +18.06
  [−0.8, +24.7]**; DT −33.34 [−50.1, −7.0] → −31.74 [−53.7, +23.2]. The pooled ordering depends on an
  unregistered cleaning rule; the DT interval crosses zero.
- 2026-09-25: **A8.** Panel (drop 3 training cities, 10 draws): pooled first2 17.6 / 21.6 / 31.4 (min/med/max),
  bg − first2 −0.4 / +0.6 / +9.0, DT −36.6 / −29.9 / −25.5 (direction stable; shift vs the same cities up to
  7.9 points). **Learner seed (HGB random_state 1–5, which sets the early-stopping split): pooled first2
  11.2 / 20.6 / 23.0** — the headline magnitude of the first stations moves by 12 points on an arbitrary seed,
  because every gain is measured against a Bud0c whose quality varies. DT −38.0 / −34.5 / −29.6.
  ⇒ **Headline estimand for the paper (post hoc, declared): Bud0c bagged over 5 learner seeds (median
  prediction) AND per-city effects averaged over 21 station splits**, with city + cluster bootstraps.
  `split_averaged_ladder.py --bag 5`. Report A6 as a sensitivity beside it.
- 2026-09-25: **Colombo re-run on the corrected frame (GHAP, shared builder):** RMSE 10.04, seasonal r 0.919,
  bias **+1.4 %** (prior < 15 % HELD), R² vs climatology **−0.634** (prior > 0 REFUTED). Verdicts unchanged
  (old −4.4 % / −0.699).
- 2026-09-25: **C4 done — `#writing/registrations.json` rewritten** (backup in `_backup_pre_verify_2026-09-25/`):
  seven run registrations hold **48 predictions: 26 held, 17 refuted, 5 not tested / not adjudicable**
  (was 38 / 25 / 13). Per-entry `_audit_2026_09_25` notes; amendment 3 (79qkw) added as pending; the two
  stale discrepancy notes replaced. The totals block is consistent with its rows (the check `t_tables.py`
  runs). Retire "11 registrations, 13 of 38 refuted"; there are 12 registrations lodged (incl. 79qkw).
- 2026-09-25: **F.88 learner test re-run (shared builder, both streams, paired effects added).** MAIAC:
  Bud0c RMSE 18.3–27.4; first-two gain 22.5 / 22.5 / 25.5 / **41.3** (HGB, shallow HGB, RF, Ridge) — the gain
  of the first stations is a property of how weak the sensorless baseline is; stations 3–6 0.09–0.24
  (robust null); background 36.8–39.8 (robust); pooled bg − first2 +2.2 / +2.9 / +1.5 / −11.2; DT bg − first2
  −33.3 [−50.1, −7.0] / −34.8 [−47.2, +4.8] / −32.4 [−40.9, −3.4] / −37.0 [−46.0, −13.6] (direction 4/4,
  interval 3/4). GHAP: DT −2.3 … −43.7 across learners (not stable). "Robust across non-linear estimators"
  holds for the background gain, the stations 3–6 null and the DT DIRECTION on MAIAC; it does NOT hold for
  the size of the first-station gain, which tracks baseline quality.
- 2026-09-25: **Split-averaged (21 splits) + learner-bagged (5 seeds) ladder, v1 shrinkage, site geography,
  no completeness rule.** MAIAC pooled: first2 **21.7** [9.5, 39.3] city / [7.1, 49.7] cluster; s36 0.10;
  bg **27.8** [19.6, 39.1] / [12.9, 41.6]; bg − first2 −5.3 [−17.0, +17.4] / [−24.3, +26.8].
  **MAIAC deep tropics: bg − first2 −28.7 [−34.7, −7.7] city, [−36.3, −7.7] cluster** — once split noise is
  averaged out per city, the inversion is supported (10/13 cities; median 81 % of splits per city). GHAP: DT
  +0.5 [−15.9, +12.5], pooled bg − first2 +9.3 [+0.5, +23.4] city / [−2.8, +34.4] cluster.
  ⇒ The single-split fragility (A7) was mostly split noise. Remaining question for v2: does it survive
  cross-fitted w, the 18 h rule and grid geography together? (`ladder_v2.py`, queued.)
- 2026-09-25: **Same, with the 18 h completeness rule (E5).** MAIAC pooled: first2 22.8 [9.6, 36.9]; s36 0.08;
  bg 33.6 (n 44); bg − first2 +1.5 [−5.0, +19.8] city / [−22.7, +41.1] cluster. **Deep tropics: two cities
  lose the background rung (n 11); bg − first2 −25.0 [−36.2, +8.3]** — direction kept, interval crosses zero.
  In the deep tropics many LCS stations report partial days, and the standard rule removes them. The DT
  result is sensitive to data cleaning as well as to analysis choices.
- 2026-09-25: **v2 discovery (site geography) — see redesign plan §8.** DT inversion −22.5 [−33.7, +10.8]
  reconstruction, +6.7 [−21.1, +28.3] prospective: **F.96/F.97c's inversion is demoted to exploratory.**
