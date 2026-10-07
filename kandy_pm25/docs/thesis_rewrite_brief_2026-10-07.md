# Thesis A rewrite brief (2026-10-07) — shared by every rewrite agent

**Goal.** Bring thesis A (`#writing/theses/a/thesis.md`, assembled from `#writing/pool/` and `#writing/theses/a/`)
in line with the project's current evidence, as a complete, coherent text. The author will reread and rewrite it in
his own words afterwards; write it to be correct and readable, not to be final.

**The topic does not change (author's instruction).** The title stays: *An hourly kilometre-scale fine particulate
matter reconstruction for Kandy, Sri Lanka: construction, validation without local ground truth, and measurement
priorities.* The Kandy reconstruction is the subject. The cross-city information-budget study (the "ladder") is the
evidence for **measurement priorities** and lives mainly in Appendix A ("The value of each information source,
measured across the panel"). Do not re-scope the thesis around the ladder.

## What the evidence now says (read these before writing)
- `kandy_pm25/docs/thesis_change_list_2026-10-06.md` — item-by-item list (its line numbers refer to
  `#writing/thesis/chapters/chNN*.md`; the SAME text lives in `#writing/pool/chNN_*/*.md` — edit the POOL).
- `CONTEXT.md` (repo root) — load-bearing facts, quotable numbers, and the RETIRED numbers (§3: never quote those).
- `kandy_pm25/docs/review_remediation_plan_2026-10-06.md` — the October review and every corrected result.
- Ledger `kandy_pm25/docs/model_reference/F_epistemic_ledger.md` entries F.115–F.124 (grep `^## F.11`, `^## F.12`).
- Results: `kandy_pm25/docs/{confirmation_results_2026-09-28,rich_baseline_results_2026-09-28,learner_robustness_results_2026-09-29,spatial_curve_results_2026-09-28,full_network_ladder_results_2026-10-05,spatial_curve_full_record_results_2026-10-05}.md`.
- Paper 1 reference draft (already revised on the same evidence; reuse its framing, not its sentences verbatim):
  `papers/paper1_information_budget/ai_reference_draft/` (§3.1.8, §3.2.1, §3.6.5, §4.1–4.5, §5).

Key corrected findings (F.124), to be stated wherever the old claims appear:
1. The registered rungs were not like for like: first stations only recalibrate the sensorless estimate (intercept and
   slope), the background is read on the day. H1–H5 are quoted **"as constructed"**. Read on the day, two stations of any
   kind reduce daily error by close to 58 % and the background − first two is about zero. **Never write that a
   background is worth more than local stations.**
2. Station-count curve read daily: 1/2/3/5/8 stations → about 42/53/56/58/61 %; as calibration only, about 11 % for any k.
3. The deep-tropical "inversion" / "4.2×" / "+33.3" is retracted (F.115–F.117): exploratory, direction only.
4. Spatial curve: "cities split, 15/23 cross" → 3/23 after a Holm correction; heterogeneity not significant; siting
   interval was a bug (real ≈ ±0.05, verdict holds); tropical vs other −0.22 [−0.45, +0.02]; detection limits 0.35/0.51;
   a satellite PM2.5 surface ranks like the built-up layer (ρ ≈ 0.1).
5. f ≈ 0.48 is a **bound under the coherence cap**, 0.433–0.492 across cap choices; never "fixed/resolved by physics".
6. Humidity: the FECT label used constant RH 80 %; hourly RH shrinks the diurnal swing ~11 %; the shape needs a
   reference co-location (CEA). The health burden applies GEMM to all ages (should be 25+): illustrative only.
7. Registry: 17 registrations, 14 run, 105 predictions, 66 held, 23 refuted (use the T7_5 table; never type counts).

## Mechanics (the build refuses on violations)
- **Numbers.** Every computed number must be a `{{claim:key}}` token. List keys with
  `grep -o '"v2\.[^"]*"' kandy_pm25/data/processed/modular/claims.json | sort -u` (also older keys). Ladder/review
  keys: `v2.conf.reco.*`, `v2.conf.pros.*`, `v2.rich.*`, `v2.learn.*`, `v2.fullnet.N1..N5.*`,
  `v2.review.registered_loco.reco.*` (gL2s_rmse, gBGall_rmse, BGallmL2s_rmse, …), `v2.review.full_loco.*`,
  `v2.review.registered_lono.*`, `v2.review.k.day{1..8}.*` / `cal{1..8}.*`, `v2.curve.{reg,full}.*`, `v2.f.cap_min/max`,
  `v2.rh.*`. Each interval key has `.median`, `.lo`, `.hi`. If a number you need has no key, write it in words if it is
  a count, or leave `[[NEED CLAIM: description]]` and list it in your report — do not type it.
- **Tables:** new gated tables exist: `{{tbl:T7_1_ladder_v2}}`, `{{tbl:T7_2_like_for_like_v2}}`, `{{tbl:T9_1_next_v2}}`
  (use the full name). A table or figure is placed once (token alone on a line); refer to it inline elsewhere.
- **Figures:** new tags `{{fig:confirmation}}`, `{{fig:robustness}}`, `{{fig:likeforlike}}`, `{{fig:stationdaily}}`,
  `{{fig:spatialcurve}}`, `{{fig:spatialnoise}}`. Retire `{{fig:ladder}}`, `{{fig:losses}}`, `{{fig:stationcount}}`,
  `{{fig:acquisition}}` wherever they carry superseded numbers.
- **Lint (ERROR):** no em/en dashes; no first person (I/we/our/us/my); no contractions; none of: delve, pivotal,
  crucial, vital, underscore, leverage, myriad, plethora, robustly, seamless, holistic, multifaceted, "it is worth
  noting"; no sentence starting Importantly/Notably/Moreover/Furthermore/Additionally/Overall/Ultimately/In summary/In
  conclusion; no typed "Section 4.2"/"Chapter 7"/"Appendix B" (use `{{ref:label}}` with a `{#label}` that exists); no
  "this chapter"/"this appendix" (use `{{this:label}}`). Formal thesis register, third person, no anecdotes, no
  rhetorical headings. Thesis length is not a concern.
- **Check your files** (read-only, safe in parallel):
  `cd "D:/ProjectCD/#writing" && PYTHONUTF8=1 ../kandy_pm25/.venv/Scripts/python.exe build/lint.py <files>` and
  `... build/check_tokens.py <files>`. Both must be clean for your files. **Do NOT run build_docx.py or assemble.py**
  (the coordinator runs the full build once all agents finish).
- Edit with the Edit tool. Never truncate a file in place (gotcha #81). Edit ONLY the files assigned to you. New pool
  files: name `NN-s-short-slug.md`, first line a heading with a `{#s-unique-label}`; tell the coordinator exactly which
  include line to add and where (unless the include file is assigned to you).
- Report back (under 400 words): files changed, what changed in each (one line), any `[[NEED CLAIM]]` placeholders, any
  include lines the coordinator must add, and anything you could not resolve.
