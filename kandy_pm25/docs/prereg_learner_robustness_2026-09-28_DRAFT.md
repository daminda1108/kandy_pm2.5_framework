# Pre-registration (DRAFT, not lodged) — do the confirmed ladder results depend on the learner?

**Status:** draft for the author's approval, 2026-09-28. Lodged on OSF only on the author's
instruction, and only after the rich-baseline registration (`prereg_rich_baseline_2026-09-28`),
which is independent of this one.

## 1. Question

Every gain on the ladder is measured against the sensorless rung Bud0c, and Bud0c is a gradient-boosted
tree model (scikit-learn `HistGradientBoostingRegressor`). On discovery the first-station gain ranged
from 22 to 41 % across learners, so the *sizes* depend on the learner. The confirmation paper admits
that it did not test whether the *verdicts* do. This test asks whether the confirmed verdicts
(`ueyfr`: H1, H2, H3 and H5 supported; H4 ordering background > first two) hold when Bud0c is built
by three very different learners, including a deep sequence model and a physics-informed variant.

## 2. What has been seen, disclosed in full

The PM2.5 of every city has been analysed with the HGB learner (discovery many times; confirmation
once, `ueyfr`). **No other learner has been fitted to these cities' real PM2.5 under ladder v2.** The
code of every learner is tested only on a synthetic outcome independent of every predictor before
lodging. The predictions are made knowing the HGB results and are blind to how they change with the
learner.

## 3. Cities and features (nothing new selected)

The same union as the confirmation: all cities of the discovery and confirmation panels (leave-one-city-
out over all of them), with **Bud0c's features only** (7 drivers, 60 urban-centre geography features,
MAIAC AOD). The rich-baseline streams are **not** used here, so the two tests answer separate
questions. **Primary panel: the 72 confirmation cities.** Discovery and pooled beside them.

## 4. Learners (each replaces only the Bud0c learner; everything above it is unchanged)

| id | learner | details fixed now |
|---|---|---|
| **L0** | HGB, as confirmed | unchanged (`ladder_v2.bagged_bud0`); reproduced through the same injection path as the others (parity gate) |
| **L1** | TabPFN regressor 8.5.0, v3 weights (tabular foundation model) | per leave-one-city-out fold, **10,000 training rows**, drawn with an equal count per training city (seeded); `n_estimators` default; `inference_precision=float32`; Kaggle T4 GPU; all folds in one environment |
| **L2** | Sequence neural network (deep learning) | a GRU (2 layers, 64 units) reading the previous **14 days** of the daily features (missing days as zeros plus a missing-indicator channel), concatenated with the static geography through a 64-unit dense layer; loss = mean squared error on standardised PM2.5; Adam, learning rate 1e-3, batch 512, up to 40 epochs with early stopping on a 10 % random hold-out **of training cities**; PyTorch deterministic mode, fixed seeds; Kaggle T4 GPU |
| **L3** | HGB with physics-informed features | L0 plus four features derived only from Bud0c's own drivers: ventilation coefficient `vc = BLH × wind`, `1/vc`, its 3-day trailing mean (stagnation memory), and `AOD / BLH` (column-to-surface scaling) |

Each learner uses the same **five seeds** and the Bud0 prediction is the median over seeds, as in L0.
No hyperparameter is tuned on these cities; the settings above are fixed now.

## 5. Estimator above Bud0 (frozen, unchanged)

`ladder_v2.run` (code `e6b744b`) with its Bud0 step supplied by each learner's out-of-city predictions
(`scripts/ladder_v2_learners.py`, frozen by SHA-256 before lodging). 21 splits, cross-fitted weights,
18-hour completeness, 4,000-draw two-level cluster bootstrap. **Parity gate:** L0 passed through the
injection path must reproduce the registered confirmation's per-city effects to 1e-9, or nothing is
written.

## 6. Endpoints and predictions (reconstruction arm, RMSE unless stated; confirmation panel)

For **each** of L1, L2, L3:

| id | quantity | rule | prediction |
|---|---|---|---|
| **Lk-H1** | first two stations | cluster lower bound > 0 | **supported** |
| **Lk-H2** | stations 3–6 | cluster interval inside [−1, +1] | **supported** |
| **Lk-H3** | background given six | cluster lower bound > 0 | **supported** |
| **Lk-H4** | background − first two (two-sided) | ordering claimed only if the interval excludes 0 | no direction predicted |
| **Lk-H5** | background − first two, exceedance loss | cluster lower bound > 0 | **supported** |
| **Lk-B** | the learner's Bud0 RMSE against L0, % per city (positive = better than HGB) | two-sided; a difference claimed only if the interval excludes 0 | **L1, L2: no improvement over HGB claimed** (interval includes 0 or favours HGB); **L3: no prediction** |

Fifteen verdict tests and three skill comparisons; no multiplicity correction; each reported against
its own rule. The summary statement "the confirmed verdicts do not depend on the learner" is made only
if all twelve directional verdicts (H1, H2, H3, H5 × three learners) are supported.

**Secondary (not counted):** discovery and pooled panels; the prospective arm; the tail loss; the paired
change of each effect against L0.

## 7. What the outcomes would mean (written before the data)

- All twelve verdicts supported → the confirmed ranking is a property of the observations, not of the
  learner, and the paper can say so.
- A verdict fails for one learner → the paper reports that the finding holds under tree models but not
  under that learner, with the size.
- L2 beats L0 on Bud0 skill → multi-day memory carries information the daily trees miss; the ladder's
  gains above Bud0 are then overstated for that reason, and the size is reported.
- L3 changes little → the trees already learn the ventilation physics from BLH and wind.

## 8. Reproducibility and deviations

GPU arithmetic may differ across machines (see OSF `4qs9c` §5), so L1 and L2 are computed in one Kaggle
environment, the package versions are pinned and printed, and one fold per learner is run twice to
report run-to-run agreement. Deviations are logged with date and reason before scoring and reported
beside the registered result.
