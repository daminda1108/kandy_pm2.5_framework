# Network-constraint audit and redo plan (2026-10-04)

**Why.** Until 2026-10 the project ran on a slow, unreliable connection. The user now has a fibre line with
**unlimited free download 00:00–04:00 SLST** (UTC+5:30), and uploads (including Kaggle datasets) are no longer
constrained. Directive (user, 2026-10-04): redo everything that was stalled, rescoped or downsized for network
reasons; schedule heavy downloads inside the night window; record everything.

**Method.** Three read-only searches (code and constants; session log, memory and CLAUDE.md archives; plans,
registrations and deviation logs), then every lead that could touch a result verified against files and data.

## A. Still shaping current results

| # | Compromise | Where | Effect, verified 2026-10-04 | Disclosed? |
|---|---|---|---|---|
| A1 | OpenAQ ingest capped at **12 stations and the city's last 2 calendar years**, "to keep the whole sample near 3 h" | `scripts/ingest_openaq_sample.py:48-53` (docstring still says 30; stale); reused by `ladder_v2_confirm.py` | Binds in **45/63** OpenAQ confirmation cities (median 17 available, max 655); all **46** discovery OpenAQ files have ≤ 12 stations. In a 12-station city: 4 held out, 6 rung, **1–2 stations form the background rung**. 4 confirmation cities had no background rung. Confirmation window loses 2024-09 → 2024-12. The "median 12 stations per city" scarcity cited for the station-frame spatial nulls (F.103, F.105, F.111, 636 stations) is partly this cap. | Cap stated as a rule in `ueyfr` and Paper 1; **download motive not stated** (fixed in the Paper 1 draft 2026-10-04 with a [DISCLOSE] note) |
| A2 | Spatial learning curve downloaded **one year per site** ("best one-year window only, ~2.5 h", plan D2) | `spatial_learning_curve_plan_2026-09-11.md` D2; `spatial_curve_freeze.py` (365-day window, 75 % presence) | **21 of 62** candidate clusters lost more than half their sites at the window step, **14 lost all**. Tropics hit hardest: Bangkok 86 → 11 sites (one year downloaded; median site 158 complete days), Colombia (deep tropical, 19 sites), Mexico, India, Vietnam and two Brazilian clusters lost. The registered frame has **1 tropical city**. | Window registered; **cost motive not stated** |

## B. Smaller items still open

| # | Item | Status |
|---|---|---|
| B1 | Precipitation ladder (`z89kt`): all 11 CNEMC cities excluded, ERA5-Land precipitation never pulled for them | IMERG now exists for every city (`rich_streams/imerg`); exploratory re-run possible |
| B2 | Premasiri (2010) five-site Kandy pixel test: never run, Overpass unavailable twice | Small; ledger notes reduced value after F.76 |
| B3 | Ladder drivers: BLH as the mean of 4 synoptic hours (cost), not 24 | Low expected effect; robustness check possible |
| B4 | Paper 1 §2.10 table lacked D-2 (compute, not network) | **Fixed 2026-10-04** |
| B5 | Panel-expansion census quality metrics on ≤ 10 stations per cluster (API rate limit) | Screening only; low |

## C. Resolved and verified equivalent (no action)
Overpass → Geofabrik (spatial curve D-6; 7 confirmation cities; identical where computed both ways) · FIRMS
toBands aggregation (identical) · CDS monthly chunking (no loss) · spatial-curve S3 throttling (re-fetch, 0 failed
objects) · DNS outages (resumed from cache; confirmation audit 0.00 % loss) · confirmation ingest sharding (E-1) ·
OSF silent non-creation (gotcha #100) · wave-2 uploads (done).

## D. Not affecting current claims
China per-city roads major-only (retired 199-city census; the spatial-null frame pulls all road classes, verified
in `build_lur_predictors.py`) · trajectory archive 12 GB → 0.5 GB ERA5 subset (Kandy transboundary claim; no
equivalence test; low) · EDGAR, PVAF B2/B4, t925 (retired stages) · PurpleAir credits (cost, not network).

## Redo plan (approved in principle by the user 2026-10-04; each registered test needs its text approved)

| Step | What | Type | Download (night window) |
|---|---|---|---|
| A | **Full-network ladder**: all qualifying OpenAQ stations (cap 40), full driver windows, discovery + confirmation; frozen estimator; verdicts + paired change vs the 12-station results | registered before download | ~1.6–2.2 M daily files, est. 2–3 nights |
| B | **Spatial curve full-record frame**: full records for every candidate cluster, same freeze rule, score the frame that results | registered amendment before download | ~2–3 M objects, est. 2–4 nights |
| C | Station-frame spatial nulls (siting, families, embeddings) on full networks | exploratory, reuses A | none extra |
| D | Precipitation re-run with IMERG; Premasiri pixel test; hourly-BLH sensitivity | exploratory | small |

Night runner: `scripts/night_window.sh` (starts after 00:05 SLST, hard stop 03:50, resumable, atomic per-city writes).
