# Writing log — Paper 1 (information-budget ladder / generalizable methods)

Dated entries, reverse-chronological is NOT required here (append at the bottom, like a diary,
so the order of work is easy to follow). This log is for the WRITING process only — model
results and project narrative stay in `memory/SESLOG.md`.

---

### 2026-09-23 — workspace created, Introduction drafted

- New directory `D:\ProjectCD\papers\` created, separate from the old `docs/paper/` drafts and
  the `#writing/` thesis pool (user was unsatisfied with earlier attempts — this is a clean
  restart, not a rebuild).
- `WORKFLOW.md` written: house style (explain figures in depth before showing them, standalone
  captions, generous citation, immersive-but-formal tone, modular files, OK to leave sections
  incomplete, `[F.xx]` traceability markers during drafting).
- `references.bib` seeded from `kandy_pm25/docs/paper/references.bib` (already verified,
  field-checked bibliography shared with the thesis) — extend, don't restart, the citation base.
- `figures/FIGURE_PLAN.md` written with the 8-figure plan from
  `docs/paper/publication_strategy_2026-09-23.md` §3, each entry expanded with a caption draft
  and a "figure-introduction paragraph" placeholder per the new house style.
- `manuscript/01_introduction.md` drafted in full (see file for status). Uses the audited
  numbers from the 2026-09-23 ledger-audit subagent pass (48-city panel, ladder gains, the
  8 registered nulls) and positions against Choi & Hummel (ERL, Jan 2026) and the
  AlphaEarth/Quito paper (Alvarez et al. 2025) per the literature research already done this
  session.
- **Next session should:** draft `02_methods.md` (the tier contract, admits/estimates/imposes,
  the 48-city panel construction, the estimator families) — this is mostly description of
  already-built machinery (`src/modular/`), lower risk than Results. Then `03_results.md`,
  which needs the C7 fix decision resolved first (see publication_strategy doc §2) before the
  ladder-gain numbers can be called final — draft with `[F.xx]` markers and the current numbers,
  flag clearly that F.97/F.109/F.112 numbers are pending the city-3147 re-score.
- Spatial-curve (E8/E9) debugging is running in a separate session ("Workflow optimization
  tools") in parallel; not a blocker for this paper per WORKFLOW.md's division-of-labor note.

### 2026-09-23 (same day, later) — MAJOR: headline finding reframed mid-session

The parallel session fixed the C7 city-3147 stream-completeness defect (it was silently NaN-
filling geography features into `ladder_order_and_bootstrap.py`, `loss_sensitivity.py`,
`precip_ladder_test.py`) and regenerated `claims.json` (566/566 claims reproduce exactly). While
re-scoring, it ran a NEW paired-within-city test on the full 48-city panel — not previously done
— comparing the background-monitor tier against the two-sensor tier:

- **On GHAP** (fused, monitor-blended satellite product): paired background−first-two = **+14.6
  [+3.1, +27.2]**, background wins 32/46 cities. Holds.
- **On MAIAC** (raw, the "honest" stream this project switched to after F.95 specifically
  because GHAP partially encodes the ground stations it's compared against): paired = **+2.3
  [−10.9, +21.4]**, wins 24/46. **Does not survive pairing** — the pooled/unpaired "background is
  the largest lever" headline is itself an artifact of the same failure pattern as gotcha #91
  (median-of-medians vs. paired-within-unit), now confirmed a third time on new data.
- **Deep-tropical band only, MAIAC** (ledger F.97c; first computed 2026-09-01): paired =
  **−33.3 [−50.1, −7.0]** — **local sensor beats background in Kandy's own climate band**,
  robustly. **CORRECTED 2026-09-23 (peer session caught my error here): this is NOT
  pre-registered.** F.97c's own ledger text says "the pairing test was not pre-registered;
  report as post-hoc" — an earlier CLAUDE.md summary that implied otherwise was itself wrong.
  `bkpyr` (the relevant OSF registration) covers C1/S3, S1, S2, R2, R3 only — no band-inversion
  or R1 test. Both this result and the panel-wide MAIAC pairing test above are **exploratory,
  full stop.** The registrations that did test ladder predictions are `g6hqb` (re-validation)
  and `z89kt` (precipitation) — see `D:\ProjectCD\#writing\registrations.json` for verdicts.

**This changes Paper 1's headline finding, for the better.** The defensible story is no longer
"a regional background monitor is the single biggest lever" (true only on the less-trustworthy
fused product) — it's (a) a general methodological point that pooled/unpaired panel comparisons
overstate a tier's advantage, demonstrated three times over in this project's own results, and
(b) a band-specific, robust, pre-registered result that in the deep-tropical band a local sensor
outperforms a regional background monitor, which is both the more interesting finding and the
one most directly relevant to Kandy (ties Paper 1 and Paper 2 together).

**Caveats flagged by the peer session, both encoded in `01_introduction.md`'s status header:**
- **Both pairing results (panel-wide MAIAC, +2.3 [−10.9,+21.4], AND deep-tropical, −33.3
  [−50.1,−7.0]) are exploratory / post hoc — I initially mis-stated the deep-tropical one as
  registered; corrected 2026-09-23 after the peer session caught it.** Neither may be called
  "registered" or "pre-registered" anywhere in the manuscript.
- `claims.json`'s own F.112 annotation is stale (still implies "P4 held") and the old
  `#writing/` thesis prose carries now-false "fragility"/"twenty times" language — neither
  should be copied into this paper; trust the computed CIs above.

**Drafted this session:** `00_title_abstract.md` (draft), `01_introduction.md` (full draft,
built around the reframed finding, numbers marked PROVISIONAL pending an F-code), `02_methods.md`
/ `03_results.md` / `04_discussion.md` (outline stubs — `03_results.md`'s §3.1/3.2/3.4 are
explicitly blocked pending the ledger write-up).

**Next session should:**
1. Check whether the peer session has assigned an F-code and written the pairing result into
   the ledger — if so, un-mark PROVISIONAL in `01_introduction.md` and fill in `03_results.md`
   §3.1, 3.2, 3.4 with final numbers.
2. Draft `02_methods.md` in full (not blocked by the above — can proceed independently), adding
   the new §2.6 "why paired, not pooled" subsection this finding motivated.
3. Add the three ledger instances of the pooled-vs-paired discrepancy (gotcha #91 and its
   siblings) as a concrete list for Discussion §4.2 — pull exact F-codes/values from the ledger.
4. Decide the format for Results §3.5 (one subsection per null test vs. a summary table + 2-3
   call-outs).
5. Build F1 (framework schematic) and F2 (panel map) — neither depends on the moving numbers,
   good candidates to build now while Results is blocked.

### 2026-09-23 (same day, later still) — style pass: removing AI-typical cadence

User flagged that the first draft read as AI-generated: 47 em dashes across
`00_title_abstract.md` and `01_introduction.md`, plus the connective-tissue filler and
repeated rhetorical shapes that usually come with them. Added a permanent checklist to
`papers/WORKFLOW.md` ("De-AI-ifying the prose") and did a full rewrite pass on both files, not
a punctuation find-and-replace — the underlying sentence rhythm needed to change, not just the
dash. Verified with `grep` afterward: zero em dashes remain in either file's actual prose (one
each remained only in the internal `[STATUS: ...]` working note, since fixed too).

This checklist applies to every section drafted from here on, including the reframed §1.3
content and everything in `02_methods.md` onward. Re-run the grep check before calling any
section done.

### 2026-09-28 — confirmation results in; results, discussion, conclusions, abstract and evidence map drafted

Confirmation (OSF ueyfr) scored once: H1 +8.5 [3.1, 25.1], H2 +0.22, H3 +41.1, H4 +24.6 [4.1, 47.8]
(background > first two), M1 undetectable, H5 +59.3. Drafted in `ai_reference_draft/`: 3.1 (registered
confirmation), 3.2–3.5 and 3.7 (discovery, exploratory), 4.1–4.5, 05, 00 abstract, 90 evidence map.
Corrections made while writing: the GHAP "deflation" claim (contribution 3, §1.2) does not survive v2
pairing and was rewritten as a tilt of the ordering; methods 2.6/2.10 had a stale freeze commit
(ba0da66, 23 files → e6b744b, 27) and placeholder OSF ids; amendment 3 is 4qs9c. Em-dash grep: only
status lines and empty table cells. Still to write: 3.6 (spatial curve, pending), 06 statements,
07 figures/tables plan, 08 supplement, 91 references.
