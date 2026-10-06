# Amendment 1 to OSF `rqn4y` — deep-learning arms for the spatial learning curve

**Lodged before any real-data scoring.** Project: Kandy PM2.5 (Daminda Alahakoon, University of
Peradeniya). Drafted 2026-09-11. Parent registration: OSF
[`rqn4y`](https://osf.io/rqn4y/), *Pre-registration: what each additional monitor buys for the
within-city PM2.5 field*. Plan: `kandy_pm25/docs/spatial_curve_dl_arms_plan_2026-09-11.md`.

**OSF [`26hp8`](https://osf.io/26hp8/), project [`w6kep`](https://osf.io/w6kep/)**, registered
2026-09-11 01:30:15 UTC by `scripts/osf_lodge.py` and verified as an artefact after the request.
Submitted pending OSF approval; the timestamp is fixed at submission. At lodging the frame had not
been frozen and no real PM2.5 value had been scored.

This amendment **adds** estimators and predictions. It changes nothing in the parent registration.
Every estimator, prediction, stop rule and detection limit registered there stands as registered.

---

## 1. What had been done when this was lodged, disclosed

- **The frame had not been frozen and no real PM2.5 value had been scored by any estimator.** The
  download (D2) was still in progress.
- **Machinery was checked on synthetic data only.** A simulated 60-site city carrying an
  exponential Gaussian random field (correlation length 4 km) was scored with the parent's
  estimators E0–E6. Fitted-variogram kriging reached a median held-out rank correlation of 0.540 at
  35 fitting sites against 0.554 for oracle kriging given the true variogram. The first version of
  this check required 0.5, a number chosen without reference to the oracle, and it was replaced by
  the oracle-referenced criterion **before any real data were scored**. The change concerns a
  synthetic machinery check and no registered quantity.
- **Four implementation deviations from the parent** were declared in the analysis code
  (`scripts/spatial_curve_analysis.py`, D-1 to D-4) before any real result existed: cLHS ordering
  is drawn per *k* because it has no nested form; Q2 runs at 20 replicates × 60 shared days; GWR and
  the blocked held-out set run on random ordering only; Q3's reach is defined on E3, with E4 beside
  it. They are restated here so that they are on the public record before scoring.

## 2. Estimators added

All four are scored on **exactly the parent's splits**: the same random seeds, held-out sets and
fitting sets as E0–E7, so every comparison with the parent's estimators is paired within
replicate.

| | estimator | training |
|---|---|---|
| **E8** | TabPFN regressor, the `tabpfn` package's default regression weights at run time (package 8.5.0 at lodging), default settings, no tuning. Features: the seven registered covariates and local x, y in km. | none: in-context on the *k* fitting sites |
| **E9** | E8 plus one feature: the ordinary-kriging prediction at each site. For fitting sites it is computed **leave-one-out** from the other fitting sites; for held-out sites from all fitting sites. | none |
| **E10** | Convolutional Gaussian neural process, deepsensor `ConvNP` with `likelihood="gnp"`. Context, in this order: (i) a gridded auxiliary raster of the benchmark covariate, built-up land cover within 2.4 km; (ii) the fitting sites, carrying PM2.5 and the seven covariates as columns. Targets: the held-out sites. | across cities, Section 3 |
| **E11** | Transformer neural process, diagonal variant (TNP-D; Nguyen & Grover, ICML 2022, arXiv 2207.04179), adapted from the authors' MIT-licensed implementation. Inputs per point: x, y and the seven covariates. | across cities, Section 3 |

**Leave-one-out in E9 is required, not optional**: in-sample kriging reproduces a site's own value,
which would place the target inside its own feature.

**How E10 takes covariates, verified before lodging.** A probe of deepsensor with the project's
own construction (`DataProcessor(x1_name="lat", x2_name="lon")`, frames indexed `(time, lat,
lon)`) established two facts. A context made only of point frames **fails** in the library's
coordinate normalisation, so **at least one gridded input is required**. Point covariates are
accepted **as extra columns of the station context frame**, which is how the project's earlier
ConvCNP carried its covariates. Hence the construction above. One consequence is stated here, not
discovered later: covariate values **at the held-out sites** reach E10 only through the gridded
channel, because target sites carry no inputs of their own. The raster is built from the same
source, radius and reduction scale as the site covariate.

## 3. Training of E10 and E11

- **Training data: daily fields.** For a training city and a UTC day, one task draws *k* from the
  registered sizes {3, 5, 8, 12, 18, 25, 35, 50, 70} truncated at the sites present, takes *k*
  present sites as context and the remaining present sites as targets. Daily fields give on the
  order of 10⁴ tasks; static means would give about 30, too few for a neural process.
- **Folds: five, grouped by country**, so that no national network appears on both sides of a
  split. Every frame city is scored by the models whose training folds exclude its country.
- **Validation for early stopping** uses cities drawn from the training folds only, never the test
  fold.
- **Seeds: three per fold.** Every reported E10 and E11 value is the median over seeds, with the
  seed spread reported beside it.
- **Scoring.** Q2 directly. Q1 by conditioning on the fitting sites' window means and predicting
  the held-out sites' window means.
- **Compute:** Kaggle GPU.

**Deep-learning positive control, registered.** Before any real scoring, E10 and E11 are trained on
synthetic cities carrying Gaussian random fields of known variogram, and scored on synthetic cities
unseen in training. **Each must come within 0.05 of oracle kriging at 35 context sites.** A model
that fails this is reported as a **failure to train**, and its real-data results are not
interpreted as evidence about the method: a null from a model that cannot learn a known field says
nothing about the field.

## 4. Compute budget for E8 and E9, declared

TabPFN on CPU is on the order of a second per fit. E8 and E9 therefore run the parent's **primary**
Q1 design only (random ordering, random held-out, 100 replicates, every registered *k*) and Q2 at
**10 replicates × 20 shared days**. If a GPU is used, the budget does not change, so that E8 and E9
are scored identically however they are run.

## 5. Predictions

Detection limits are the parent's: the registered Wilcoxon method at a between-city spread of 0.20,
evaluated at the number of countries in the primary frame.

- **X9.** No deep estimator (E8, E9, E10, E11) exceeds E5, regression kriging, by more than the
  detection limit at any registered *k* in the primary frame.
- **X10.** E9 beats E8 at every *k* ≥ 12 in the primary frame.
- **X11.** For E10 and for E11, the paired advantage over E3 at *k* = 3 and 5 exceeds the advantage
  at the two largest registered *k* the city allows, in the median primary city.
- **X12.** E10 and E11 differ by less than the detection limit at every registered *k*.
- **X13, exploratory.** E10 and E11 on the band arm, against the primary-frame envelope.

## 6. What each outcome means, written before the outcome is known

- **X9 holds.** The most promising deep methods do not break the spatial limit either. Chapter 8's
  conclusion holds across the classical and the deep families.
- **X9 fails.** A deep method recovers structure the classical families cannot, and the thesis
  reports at which density it does so.
- **X11 holds.** Cross-city deep priors are worth most at low density — where Kandy sits, with two
  sensors.
- **X11 fails.** The learned prior carries no transferable spatial structure, which sharpens
  Chapter 5's account of why the project's earlier ConvCNP produced smoothed-out maps.
- **X12 holds.** Two structurally different architectures agree, so whatever limit they meet
  belongs to the data rather than to one inductive bias.

## 7. Deviations

Any departure from this amendment is reported beside the result it affects, with its reason. A
step that cannot be run is reported as a failure to test, not replaced by an alternative chosen
after the data are seen.
