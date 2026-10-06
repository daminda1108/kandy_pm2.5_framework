# Amendment 3 to OSF `rqn4y`: E8/E9 (TabPFN) are scored on CPU only (D-8)

**Lodged before any E8/E9 verdict, and before any pooled summary of any estimator, was computed.**
Project: Kandy PM2.5 (Daminda Alahakoon, University of Peradeniya). Drafted 2026-09-23. Parent
registration: OSF [`rqn4y`](https://osf.io/rqn4y/). Amendment 1: OSF [`26hp8`](https://osf.io/26hp8/)
(deep-learning arms, which registered E8/E9). Amendment 2: OSF [`4whsc`](https://osf.io/4whsc/).

Lodged on OSF by `scripts/osf_lodge.py`; the identifier and timestamp are those OSF assigns to
this registration.

**OSF:** registration [`4qs9c`](https://osf.io/4qs9c/), project [`79qkw`](https://osf.io/79qkw/), registered
2026-09-28 08:43:26 UTC (pending OSF approval at lodging).

**Lodging note, 2026-09-28 (read with §5).** This text was first submitted on 2026-09-23 12:51 UTC
(project `79qkw`). OSF logged the submission but never created the registration; the draft stayed a
draft, which was found on 2026-09-28. It is registered now from the same project and draft. §§1–4
are the 2026-09-23 text, unchanged. §5 discloses everything done between the two dates, including
one statement in §2 that turned out to be wrong.

This amendment **fixes the device on which E8 and E9 are computed**. It changes no estimand, no
estimator family, no hyperparameter, no prediction, no pass criterion, no stop rule and no
detection limit in `rqn4y`, `26hp8` or `4whsc`. The deviation was declared in code on 2026-09-15
(`DEVIATIONS`, D-8, in `scripts/spatial_curve_analysis.py`, written into every run's summary);
this amendment puts it on the public record before the result exists.

---

## 1. What had been done when this was lodged, disclosed in full

- **E0–E7:** per-city results exist for all 78 city-frames (37 registered, 41 S-1), stored as
  per-city files. **They have not been pooled.** No curve, no median, no increment and no verdict
  has been computed for any estimator.
- **E10 (ConvGNP):** passed its registered positive control; real-data predictions exist
  (952,068 rows). Training logged the early-stopping validation loss that `26hp8` specifies. **No
  held-out skill has been summarised.**
- **E11 (TNP-D):** failed its registered positive control (recorded in amendment 2); its
  real-data results are not interpreted.
- **E8/E9 on GPU (2026-09-14):** 27 cities (19 registered, 8 S-1) were scored on a Kaggle T4
  before the device dependence below was found. **These rows are archived, never merged and never
  resumed from.**
- **Values seen while diagnosing the device dependence:** 48 per-task E8/E9 Spearman values, each
  computed on both GPU and CPU, were compared to establish §2. They were read as a reproducibility
  check (agreement between devices), not as skill, and no summary of them was formed.
- **Values seen while testing the CPU pipeline (2026-09-23):** three local smoke runs of the CPU
  scorer, of 3, 5 and 25 tasks from the first city of one shard, printed per-design medians over
  6 to 50 rows. These are timing and plumbing checks on a trivial fraction of one city and carry
  no information about the verdict.
- **E8/E9 on CPU:** running on Kaggle at lodging (five kernels, `kandy-e89-cpu2-*`), every task
  re-scored from the start.

## 2. D-8: why the device must be fixed

`26hp8` fixes TabPFN to its **package defaults** (`TabPFNRegressor(random_state=SEED)`) but does
not fix the device. In the installed version (tabpfn 8.5.0, v3 default weights) the default
`inference_precision="auto"` turns on **mixed-precision autocast on CUDA** and runs **float32 on
CPU**. "Package defaults" are therefore a different numerical estimator on each device.

**Measured** (same package version, same weights, same seed, same tasks):

| comparison | tasks | identical | median abs. difference in Spearman | max |
|---|---:|---:|---:|---:|
| GPU against CPU | 48 | 8 | 0.073 | 0.376 |
| CPU against CPU | 48 | 48 | 0 | 0 |

A difference of 0.073 in a per-task Spearman is the same order as the effects the registration
sets out to detect, so the device cannot be left to chance.

**Choice: CPU only.** CPU is deterministic run to run, reproducible on any machine, and carries no
accelerator quota. The scorer refuses to run if a CUDA device is visible
(`scripts/spatial_curve_dl_tabpfn.py`), so a GPU cannot be used by accident.

**Consequence:** every E8/E9 task is scored on CPU. The 27 GPU-scored cities are archived and
excluded. No mixture of devices enters any result.

## 3. An implementation correction recorded with it (no change to what is computed)

The Kaggle wrapper that launches the CPU scorer collected every TabPFN `partial_*`/`pred_*` file
from all attached inputs for resumption. One GPU-era file,
`partial_tabpfn_registered_run1.parquet`, is part of the data bundle `kandy-spatial-dl-data`
(version 8). The wrapper's own D-8 check then refused to start, so no CPU run began. Corrected
2026-09-23: GPU-era files are excluded before anything is copied, named in each run's log and
summary, and an assertion keeps them out of the resume directory. This enforces D-8; it does not
alter any computation.

## 4. Deviations recorded in code, restated

D-1 cLHS drawn independently per k (not nested) · D-2 Q2 at a reduced, shared budget · D-3 E6 and
the blocked held-out on random ordering only · D-4 Q3 reach defined on E3, E4 beside it · D-5 E7
scored on held-out sites inside the grey-box grid only, every estimator re-scored on that subset ·
D-6 road covariates from Geofabrik extracts (amendment 2) · D-7 leakage self-test implementation
corrected, criterion unchanged (amendment 2) · **D-8 E8/E9 on CPU only (this amendment)** · S-1
declared sensitivity frame at 70 per cent coverage, reported beside the registered result.

---

## 5. Addendum, 2026-09-28: what happened between the first submission and this registration

- **The first CPU run produced nothing (2026-09-23/24).** The kernels installed tabpfn without a
  pinned version and received **9.0.0**, whose weights require a separate licence. Every fit raised
  an error, which the scorer caught per task, so the run finished with **0 finite values**. It is
  archived and excluded. The kernels now pin **tabpfn 8.5.0**, the version named in §2, and run a
  canary fit that refuses any other version, as well as refusing any output that is all missing.
- **The second CPU run (wave 1, 2026-09-24/25) scored part of the design.** E8/E9 predictions exist
  for 28 of 37 registered and 36 of 41 S-1 city-frames. Six shards hit Kaggle's 12-hour limit.
  **Wave 2**, covering the remaining 14 city-frames on the same Kaggle CPU environment, started on
  2026-09-28 before this registration was completed.
- **Values seen since 2026-09-23.** To test whether CPU results reproduce across machines, 80
  wave-1 tasks were re-scored on a laptop with the same code, data, package version and seed, and
  their per-task Spearman values were compared with Kaggle's. The comparison was read as agreement
  between machines, not as skill. No median, curve, increment or verdict has been computed for E8,
  E9 or any other estimator, and none will be before wave 2 is complete.
- **§2 is corrected on one point.** "Reproducible on any machine" is **wrong**. The laptop matched
  Kaggle on **1 of 80** tasks (median absolute difference in per-task Spearman **0.012**, maximum
  **0.29**). CPU scoring is deterministic *within* one machine (the 48/48 check in §2) but not
  identical *across* machines. The cause, which may be the PyTorch build or the CPU instruction set,
  has not been isolated. **Consequence:** every E8/E9 result comes from one environment, the Kaggle
  CPU image used for waves 1 and 2. No city mixes machines, and the laptop values are used for
  nothing but this check. The choice of CPU stands, because a GPU is not deterministic even on
  one machine. Its justification is narrowed to reproducibility **within** a fixed environment.
