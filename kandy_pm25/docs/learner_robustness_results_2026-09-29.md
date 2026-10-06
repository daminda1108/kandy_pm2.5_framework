# Learner robustness — registered results (OSF `jea58`, scored 2026-09-29)

Registration `docs/prereg_learner_robustness_2026-09-28.md` (OSF `jea58`, project `mn9eg`). L1 (TabPFN 8.5.0)
and L2 (GRU) fitted on Kaggle T4s (each refit reproduced its first fold exactly; 118/118 cities, 69,609
finite predictions each); L0 and L3 locally. Frozen code re-verified. **Parity gate passed:** L0 through the
injection path reproduces the `ueyfr` per-city effects to **2.8e-14**. (L0's intervals below differ in the
second decimal from `ueyfr`'s because this run's bootstrap uses its own random stream; the per-city
values are identical.) Output `data/processed/modular/ladder_v2/learners_REGISTERED_*`.

## Confirmation panel, reconstruction, RMSE unless stated, median [two-level cluster 95 %]

| | H1 first two | H2 stations 3–6 | H3 background | H4 background − first two | H5 same, exceedance | Bud0 skill vs L0 (%) |
|---|---|---|---|---|---|---|
| L0 HGB (confirmed) | +8.53 [3.00, 25.54] | +0.22 [0.12, 0.50] | +41.10 [28.15, 62.81] | +24.58 [3.99, 44.47] | +59.33 [33.17, 67.73] | 0 |
| **L1 TabPFN** | **+18.64 [8.81, 43.19]** ✔ | +0.25 [0.11, 0.50] ✔ | +40.86 [27.71, 62.38] ✔ | **+8.32 [−5.43, +40.59]**: no ordering claimed | +59.50 [35.81, 68.36] ✔ | **−11.10 [−50.94, −1.07]** (worse than HGB) |
| **L2 GRU (deep learning)** | +11.14 [4.28, 18.11] ✔ | +0.16 [0.09, 0.30] ✔ | +39.40 [27.63, 61.84] ✔ | +25.66 [9.32, 49.34]: background > first two | +52.54 [28.46, 64.13] ✔ | +1.79 [−4.33, +8.87] (no difference) |
| **L3 HGB + physics** | +9.74 [3.19, 19.07] ✔ | +0.22 [0.13, 0.45] ✔ | +41.74 [27.55, 63.43] ✔ | +24.97 [3.12, 48.30]: background > first two | +57.73 [32.02, 67.58] ✔ | +2.01 [−0.30, +4.64] (no difference) |

## Verdicts against the registration

- **All 12 directional verdicts supported** (H1, H2, H3, H5 × L1, L2, L3). The registered summary
  statement is licensed: **the confirmed verdicts do not depend on the learner.**
- **L1-B held:** TabPFN does not improve on HGB; it is worse (−11.1 %). **L2-B held:** the GRU is no better
  than HGB (+1.8, interval includes 0). **L3-B** (no prediction): physics features change nothing
  detectable (+2.0 [−0.3, +4.6]); the trees already use BLH and wind.
- **H4 (two-sided):** the background-over-first-two ordering holds under L2 and L3 and **is not claimed
  under L1**. That is what a weaker starting estimate predicts: TabPFN's worse Bud0 makes the first two
  stations worth more (+18.6 against +8.5), which narrows the gap. The ordering therefore depends on the
  quality of the sensorless estimate; the exceedance ordering (H5) does not.

## Reading

Deep learning (a GRU over 14-day windows) and a tabular foundation model do not beat gradient-boosted
trees at this sample size, and a physics-informed feature set adds nothing detectable. Every directional
finding of the confirmation holds under every learner. The one thing that moves is the size of the
first-station gain, which tracks how good the sensorless estimate is, and with it whether the ordinary-day
ordering is resolvable.
