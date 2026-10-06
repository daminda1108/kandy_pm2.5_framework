# Proposals for the [VERIFIED] notes in the Paper 1 draft (2026-10-05)

The draft carries 11 `[VERIFIED]` notes (two more in §3.6 were already moved to Supplementary Note S3.1). Each
records a check or a correction made while the analysis was being verified. None of them should be printed as
a bracketed note. Three outcomes are possible:

- **Delete.** The note only certifies that a number was checked. The number stays in the text, and its source
  stays in `90_evidence_map.md`.
- **Supplement.** The note records a correction a careful reader may want to see. It moves to a new
  Supplementary Note S3.4, "Corrections made during verification", and the main text keeps only the corrected
  number.
- **Main text.** The note is part of the paper's argument and becomes ordinary prose.

| # | where | what the note says | proposal | why |
|---|---|---|---|---|
| 1 | §2.1, panel paragraph | the discovery-frame counts were checked on the frozen frame | **Delete** | a check marker only; the counts are generated |
| 2 | §2.1, band labels | a coding defect left 11 CNEMC cities without a band label; fixed and re-scored; band counts 13/13/11/10 | **Supplement (S3.4)**; keep the band counts in the text | every reported band result is post-fix; the history is useful but not part of the argument |
| 3 | §2.1, reference fraction | CNEMC cities had been classed as low-cost by default; fixed; 31 reference, 16 low-cost | **Supplement (S3.4)**; keep "31 reference, 16 low-cost" in the text | same reasoning as 2 |
| 4 | §2.4, admissibility | every analysis now builds its frame through one shared function, and every scoring loop names each city it skips | **Main text, moved to §2.11** as a plain design statement, without the file names | it describes how the code prevents a whole class of error, which a methods reader values |
| 5 | §2.5, cluster bootstrap | the factor 1.15 to 2.21 replaces an earlier, pre-correction 1.45 to 1.97 | **Delete** | the earlier figure was never published; only the corrected one matters |
| 6 | §2.7, leakage self-test | the lodged amendment says 22 skipped pairs; the correct count is 23 | **Delete**; already disclosed as D-7 in §2.10.2 | it would appear twice |
| 7 | §2.8, detection limits | the test-specific limits were recomputed by `mde_recompute.py` | **Delete** | a check marker only; the source is in the evidence map |
| 8 | §3.1, completeness audit | the audit result was checked | **Delete** | a check marker only (the sentence it marks now reads "a completeness audit") |
| 9 | §3.2, saturation | an earlier version reported saturation at one station (second station +0.09); with shrinkage weights borrowed from other cities, the second station is worth about a point | **Supplement (S3.4)** | an internal estimate that was never published; the corrected result is what §3.2 reports |
| 10 | §3.4, deep tropics | an earlier one-split estimate of +33.3 [7.0, 50.1] ("local stations worth 4.2× the background") excluded zero in only 3 of 20 splits | **Main text**, as one or two sentences in §3.4 | it is one of the two "striking exploratory results" that the abstract and conclusions cite as the paper's methodological lesson; the reader needs the numbers |
| 11 | §3.4, GHAP contamination | the earlier claim that GHAP "deflates the value of a local station by about half" does not survive pairing; what survives is the tilt of the ordering | **Main text**, as one or two sentences in §3.4 | the second of the two results the abstract and conclusions cite |

**Net effect:** 5 notes deleted, 3 moved to a new Supplementary Note S3.4, 3 turned into prose (one moved to §2.11).
Nothing that a reported number depends on is lost; every correction stays traceable in the ledger (F.115–F.117).

**Also fixed today, without waiting for a decision (your standing rule):** eight places described the data step
as a "download", and §2.6 said "network failures during the download lost no data". They now read "retrieved",
"retrieval" and "completeness audit". The draft no longer mentions downloads or network problems anywhere.

Say "apply" (or change any row) and I will make the edits.
