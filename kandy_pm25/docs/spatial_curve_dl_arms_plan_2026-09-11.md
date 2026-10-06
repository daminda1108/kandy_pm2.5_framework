# Plan: deep-learning arms for the spatial learning curve

**Written 2026-09-11. Nothing here has been run.** Companion to
`spatial_learning_curve_plan_2026-09-11.md` and registration OSF `rqn4y`.

---

## 0. Why now, and why before scoring

The user asked for either a promising deep-learning approach or a re-test of the ones that failed,
with Kaggle GPU time available. Both fit this test well, because the curve measures skill **as a
function of sensor count**, which is exactly the axis on which "the ConvCNP produced smoothed-out
maps" could be a density effect rather than a failure of the method.

🔴 **The order matters more than the method.** Registration `rqn4y` fixes eight estimators. If
those are scored and a deep model is then registered with the results in view, the deep arm is
post-hoc however carefully it is built. So:

1. decide the arms,
2. lodge an **amendment** registration naming them, with predictions,
3. only then score anything real — the registered estimators and the deep arms together.

The ingest continues meanwhile, because downloading involves no scoring.

---

## 1. What was checked before proposing

- **Compute.** Local torch is `2.10.0+cpu`, no CUDA. Training runs on Kaggle; the CLI is installed.
- **Existing assets.** `deepsensor` imports. The project's ConvCNP source
  (`src/stage3_pinn/models/convcnp_terrain.py`, `training/loocv_convcnp.py`) and checkpoints
  (v1, v13, assimilation) are on disk.
- **The closest published precedent does not transfer as cleanly as its abstract suggests.**
  Andersson et al. (2023, *Environmental Data Science*), the deepsensor authors' ConvGNP paper on
  sensor placement, beats Gaussian-process baselines on RMSE, likelihood and calibration. But it
  was trained on **noise-free ERA5 reanalysis** with 79 Antarctic stations, and its unseen test set
  is **unseen years, not unseen regions**. Here the target is unseen *cities*, with no dense truth
  field to train against. That absence is a plausible reason the project's own ConvCNP smoothed out,
  and the design below is built around it.
- **TabPFN** (Prior Labs) is a pretrained in-context model for small tabular problems: no training,
  default settings, a regression interface. A 2025 soil-mapping study found that adding a
  kriging-derived spatial feature ("kriging prior regression") raised R² by about 30 per cent. A
  2026 IJGIS study reports it **degrades under strong, localised spatial dependence** — the
  property this problem has. Both are stated in advance so neither outcome is a surprise.
- ⚠ **TabPFN's weights require logging in to Prior Labs and accepting its licence**, which issues a
  `TABPFN_TOKEN`. TabPFN-3 weights are non-commercial; TabPFN-2 weights carry the Apache-derived code
  licence. A thesis is non-commercial either way. **Account creation and licence acceptance are the
  user's to do.**

---

## 2. The arms

### DL-1 — TabPFN, in context (new method, no training)

- **E8** TabPFN regressor fitted on the *k* fitting sites. Features: the seven registered covariates
  and local x, y in km.
- **E9** Kriging-prior TabPFN: E8 plus one feature, the ordinary-kriging prediction at each site.
  For fitting sites it is computed **leave-one-out** from the other fitting sites; for held-out sites
  from all fitting sites. Leave-one-out is required: in-sample kriging reproduces a site's own value
  exactly, which would leak the target into its own feature.
- Runs locally on CPU: at most 70 rows per fit.

### DL-2 — cross-city neural process (re-test of the Stage B failure)

A ConvGNP from deepsensor, the project's own library, **trained across cities and applied to an
unseen one conditioned on its *k* sites**. This is the only deep design that suits fitting sets of
3–70: a network trained per city on that little data would be hopeless.

- **Training data: daily fields, not static means.** With ~30 cities, static means give ~30 tasks,
  far too few for a neural process. Daily fields give roughly 10,000 context/target tasks.
- **Task sampler:** for a training city and day, draw *k* from the registered sizes, sample *k*
  context sites, and use the rest as targets. The model sees every density it will be scored at.
- **Auxiliary context, verified by probe on 2026-09-11:** deepsensor **requires at least one
  gridded input** (a context of point frames alone fails in its coordinate normalisation), and it
  accepts point covariates **as extra columns of the station context frame**. So E10's context is a
  gridded raster of the benchmark covariate, built-up within 2.4 km, followed by the fitting sites
  carrying PM2.5 and the seven covariates. That needs one small GEE raster per city. Covariates at
  the held-out sites reach E10 only through the gridded channel.
- **Folds:** five folds **grouped by country**, so no country's network sits on both sides of a
  split. City-level folds would leak shared network behaviour (F.104).
- **Evaluation:** on Q2 directly, and on Q1 by predicting each held-out site's window mean from
  context of the fitting sites' window means.
- **Kaggle:** GPU T4 x2 per the project protocol, one kernel per fold.

### DL-3 — a second architecture, a transformer neural process

**Registered now, on the user's decision of 2026-09-11**, not conditional on DL-2. A transformer
neural process (**E11**) trained with DL-2's task sampler, the same country-grouped folds and the
same daily training data, so that E10 and E11 differ in architecture alone. It gives the deep arm a
second, structurally different member: DL-2 places context on a grid through a SetConv encoder,
while a transformer attends directly over context points. If both fail in the same way, the failure
belongs to the data, not to one inductive bias.

---

## 3. Predictions to register in the amendment, stated before any real result

- **X9.** No deep estimator (E8, E9, E10) exceeds E5, regression kriging, by more than the
  detection limit at any registered *k*, in the primary frame.
- **X10.** E9 beats E8 at every *k* ≥ 12. Tests whether the kriging prior carries the spatial
  structure TabPFN is reported to miss.
- **X11.** E10's advantage over E3 is **larger at small *k* than at large *k*.** This is what
  cross-city training should buy if it buys anything: a learned prior matters most when the local
  data are thin. A flat or reversed profile says the prior carries no transferable spatial
  structure, which would sharpen Chapter 5's account of the Stage B failure.
- **X12, exploratory.** E10 on the band arm, against its primary-frame performance.

---

## 4. What each outcome means

- **X9 holds.** The spatial nulls are not a limitation of classical estimators; the most promising
  deep methods do not break them either. Chapter 8 gains its strongest form.
- **X9 fails.** A deep method recovers structure the classical families cannot, and the thesis
  reports where on the curve it does so.
- **X11 holds.** Cross-city deep priors are worth most exactly where Kandy sits, at low density,
  which is a direct and useful result for a city with two sensors.

---

## 5. Order of work

1. User decisions: which arms; TabPFN licence; permission to lodge the amendment.
2. Lodge the amendment on OSF, verified as an artefact.
3. Implement E8/E9 locally, and pass them through the positive control.
4. Build the DL-2 task dataset from the frozen frame, and push to Kaggle.
5. Score E0–E10 together on real data.
