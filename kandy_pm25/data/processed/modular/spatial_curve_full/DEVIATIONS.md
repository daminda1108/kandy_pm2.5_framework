# Test B (OSF fu59b) — deviations, logged before scoring

## B-1 — E7 (Medellín grey-box) computed per frame (2026-10-05, before any curve was scored)
On full records the freeze rule chose different best 365-day windows for Medellín (cluster 66) in the
registered frame (2019-08-20 .. 2020-08-18) and in the S-1 70 % frame (2019-09-07 .. 2020-09-05).
`spatial_curve_greybox.py` requires one window shared by both frames (true on the one-year records) and
refused. E7 is the grey-box field averaged over the frame's analysis window, so each frame now gets its own
values: the frozen script is run on a view holding only that frame, and the analysis of S-1 reads the S-1
values (`spatial_curve_fullrecord.py`, `greybox()` and `analysis()`). On frames that share a window this is
identical to the registered computation. Seen before the decision: only the two windows (F1 reported).

## Implementation note (2026-10-05, before the summary run)
`spatial_curve_analysis.DEEP_DIRS` is set at import from the registered directory (`spatial_curve/dl_out`, which
holds the registered curve's E10/E11 predictions). The wrapper now points it at the empty `spatial_curve_full/dl_out`
and asserts that it does not exist, so no deep-arm prediction from the registered frame can enter test B's summary.
The Kaggle scoring kernels ran with `--score-only` (E0–E7 only; `merge_deep` is not called there), so no scored
city is affected.
