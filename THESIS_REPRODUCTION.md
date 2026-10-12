# Reproducing Thesis A

*An hourly kilometre-scale constrained reconstruction of fine particulate matter for Kandy, Sri Lanka: construction,
evaluation under sparse local monitoring, and measurement priorities* (A. M. D. W. B. Alahakoon, University of Peradeniya, 2026).

The version built for review corresponds to the git tag **`thesis-a-2026-10-12-r19`** of this repository: the PDF,
`VERIFICATION_thesis_a.md` and this guide were generated from the working tree that this tag commits (earlier rounds:
`thesis-a-2026-10-10`, `-r3`, `thesis-a-2026-10-11-r4` to `-r16`, `thesis-a-2026-10-12-r17` and `-r18`). Because the report is written before the commit that
contains it, the commit it names is the tag's parent; the link between the PDF, the registry and the tag is the pair of
sha256 checksums the report prints, for `claims.json` and for the assembled `#writing/build/a/thesis.md`, which anyone
can recompute at the tag. Every figure the thesis embeds was regenerated from its builder for this release, after a
review found one figure drawn from an artefact older than the field it described. The release check is a traced rebuild of every figure (`#writing/build/figure_provenance.py`, report [`FIGURE_PROVENANCE.md`](FIGURE_PROVENANCE.md)): 33 of 33 rebuilt, none drawn from a retired artefact (8 changed in this release because the field's daily cycle and interval changed, F.137). Every number in the
thesis is a token resolved from `kandy_pm25/data/processed/modular/claims.json`, which `build_claims.py` regenerates
from the scored files; the build refuses to produce a document when a stored value and a recomputation disagree.
`VERIFICATION_thesis_a.md` lists every cited claim, its source artefact and whether it rests on public or restricted
inputs. **The pipeline is designed to be reproducible; independent reproduction by a third party has not yet been
carried out.**

## Clean-environment rerun by the author (2026-10-11)

**State at `thesis-a-2026-10-12-r19`** (author's working environment, same lock file): `pytest scripts/tests` **123 passed**, 0 skipped; `build_claims.py --check` **2,748 claims reproduce exactly**, of which the thesis cites **790**, none missing from the registry (`VERIFICATION_thesis_a.md`). The Kandy chain was rebuilt end to end in the standalone release repository (`kandy_pm25_model`, `scripts/regenerate_all.py --from-anchor`), which reproduces this repository's delivered field exactly (largest difference 0.0, 2019–2023); that is a second code path by the same author, not an independent reproduction. The same test suite runs on GitHub Actions (`.github/workflows/tests.yml`, Windows); it passed on every release commit since `0767997`; the passing runs for the two most recent releases are [r12, `ff5d2c3`](https://github.com/daminda1108/kandy_pm2.5_framework/actions/runs/38146908550) and [r11, `f75233e`](https://github.com/daminda1108/kandy_pm2.5_framework/actions/runs/38141445248), and the run for this tag appears on the repository's Actions page under its commit.

**Fresh-clone rerun, recorded at `thesis-a-2026-10-11-r4`.** This is a rerun by the author from fresh clones of the public repository into empty folders, with a fresh virtual
environment built only from `kandy_pm25/requirements-lock.txt`. It is **not** an independent reproduction.

| stage | what was run | result |
|---|---|---|
| 1. environment and tests | fresh clone; `pip install -r requirements-lock.txt`; `pytest scripts/tests` | the lock as first published could not be installed (two unused packages pinned against an incompatible `botocore`; removed) and two small metadata files the tests read were untracked (added). After those fixes: **115 passed, 1 skipped** (the ladder-parity test, which needs the non-redistributed ladder frame), 0 failed. The same suite runs on GitHub Actions (`.github/workflows/tests.yml`). |
| 2. claim regeneration | `build_claims.py --check` from the clean clone's code and environment, reading the existing scored artefacts (`data/`, `results/`) read-only | **all 1,875 claims reproduce exactly**, including the 507 the thesis cites. This shows the numbers follow from the artefacts and the public code; it does not show that the artefacts themselves regenerate. |
| 3. one public result from raw inputs | the dispersion benchmark (thesis §3.3.4): for the four valley cities, station means rebuilt from the raw CNEMC archive (`extract_more_cnemc_valleys.py`) and terrain and night-light grids pulled fresh from Earth Engine (`build_valley_terrain_ntl.py`); the other six cities from their stored processed inputs, whose ingestion chain is not packaged; then `r2_score_atransport.py` and `r2b_dispersion_benchmark.py` | **identical to the thesis**: every per-city value and every median (0.371 / 0.274 / 0.393) matches with zero difference, and the rebuilt station means match the stored ones exactly. |

Not yet done: rebuilding the six older analogue cities' station inputs from raw, the information ladder from the
OpenAQ and CNEMC archives, and the Kandy chain (which needs PurpleAir access).

## Environment

- Python 3.11.1 on Windows 11; the exact package versions are pinned in `kandy_pm25/requirements-lock.txt`
  (`pip install -r kandy_pm25/requirements-lock.txt`). `kandy_pm25/requirements.txt` lists the direct dependencies.
- Document build: pandoc and Microsoft Word (the build reads page counts back from Word); the summary needs XeLaTeX.
- Earth Engine access (project of your own) for every input pulled from Google Earth Engine.
- Random seeds are fixed in the scripts (`ladder_frames.SEED = 20260927` and the per-split seeds derived from it).

## Command sequence

From the repository root, after the inputs below are in place:

```
cd kandy_pm25
python scripts/build_claims.py                      # regenerate every claim from the scored files
cd "../#writing"
python build/build_docx.py --thesis a               # tables -> lint -> assemble (claims gate) -> pandoc -> Word
python summary/build_summary.py                     # the three-page summary
python build/verify_report.py --thesis a            # VERIFICATION_thesis_a.md
```

The scored files themselves are produced by the analysis scripts in `kandy_pm25/scripts/` and `kandy_pm25/src/`.
The ones behind the main results:

| result | script(s) |
|---|---|
| Kandy field (T, B, P and the assembled field) | `src/stage1_satml/models/predict_T_anchor_v3.py` → `scripts/sharpen_T_diurnal.py` (once; it refuses a second run; hour factors from `kandy_diurnal_cea_scenario.py --write-r`) → `src/stage1_satml/decomp/build_decomp_map.py` → `scripts/build_overlay_predictions.py` → `scripts/build_spatial_uq.py` → `scripts/build_additive_field_v2.py` (interval widening from `kandy_interval_widen_fit.py`) → `scripts/build_additive_field_v3.py` |
| ten analogue cities | `scripts/xichang_prod.py --city <slug>`, `scripts/city_validation_scorecard.py` |
| information ladder (registered) | `scripts/ladder_v2_confirm.py --score`, `scripts/ladder_v2_rich.py`, `scripts/ladder_v2_learners.py`, `scripts/ladder_v2_fullnet.py` |
| like-for-like and station-count re-analyses (post hoc) | `scripts/ladder_v2_review.py`, `scripts/ladder_v2_review_k.py` |
| deployed model on the ladder (exploratory) | `scripts/pull_kandy_model_priors.py`, `scripts/ladder_v2_kandy_model.py` (spec `kandy_pm25/docs/kandy_model_rung_spec_2026-10-10.md`) |
| humidity scenario | `scripts/kandy_rh_sensitivity.py`, `scripts/kandy_rh_scenario.py` |
| local-fraction sensitivity | `scripts/kandy_f_sensitivity.py` |
| Kandy daily record (digitised) and its comparison | `scripts/digitize_nirmani_kandy.py`, `scripts/kandy_nbro_daily_check.py` |
| leave-one-sensor-out; level range | `scripts/kandy_loso_test.py`, `scripts/kandy_level_range.py` |
| CEA regulatory station (public AirShare platform; hourly stamps are UTC) and its comparison | `scripts/pull_cea_kandy_aqms.py --daily --hourly`, `scripts/kandy_cea_reference_check.py` |
| Attanayake low-cost site, model value | `scripts/kandy_attanayake_pixel.py` |
| level factor fitted to CEA 2019 → mid-2021, held-out score | `scripts/kandy_cea_level_calibration.py` (fit from a β=1 field), then `--score` after the rebuild |
| local fraction measured two ways (spec `docs/local_fraction_study_spec_2026-10-11.md`) | `scripts/pull_cea_airshare_network.py`, `scripts/local_fraction_e1.py`, `local_fraction_e2.py`, `local_fraction_e3.py` |
| where the CEA level excess enters; 2024–2026 extension check | `scripts/kandy_cea_attribution.py`, `scripts/kandy_cea_reference_check.py --extension` |
| mean conservation of the delivered field | `scripts/tests/test_conservation.py` |
| dispersion against simpler surfaces | `scripts/r2_score_atransport.py` (registered), `scripts/r2b_dispersion_benchmark.py` |
| spatial learning curve | `scripts/spatial_curve_analysis.py`, `scripts/spatial_curve_fullrecord.py`, `scripts/spatial_curve_reanalysis.py` |

## Data manifest

Third-party observations are not redistributed. Retrieval dates are the dates of the files used for the submitted
version.

| input | source | access | retrieved | used by |
|---|---|---|---|---|
| Kandy low-cost sensors (two units) | PurpleAir API (FECT records) | **restricted**: API key | to 2026-05 | T(t) training, sharpening, interval |
| Reanalysis meteorology | ERA5 / ERA5-Land via Copernicus CDS and Google Earth Engine | public, free account | 2026-04 to 2026-09 | T(t), background, ladder drivers |
| Composition model | NASA GEOS-CF via Google Earth Engine | public | 2026-05; ladder cities 2026-10-10 | T(t) prior, background, chemical check, deployed-model rung |
| Copernicus reanalysis PM2.5 | CAMS via the Atmosphere Data Store | public, free account | 2026-04 | T(t) predictor |
| Satellite aerosol | MAIAC (MCD19A2) via Google Earth Engine | public | 2026-05; ladder 2026-09 | T(t) predictor, ladder sensorless rung |
| Tropospheric NO2 | TROPOMI via Google Earth Engine | public | 2026-05 | T(t) predictor |
| Satellite PM2.5 level | van Donkelaar V6.GL.02 (WashU; sat-io collection on Earth Engine) | public | 2026-02 to 2026-06; ladder 2026-10-10 | annual level, spatial shape |
| Independent satellite PM2.5 | GHAP (Wei et al.) on Earth Engine | public | 2026-06 | level cross-check only |
| Precipitation | GPM IMERG V07 via Google Earth Engine | public | 2026-04 to 2026-07 | rain fields |
| Road network, land use | OpenStreetMap (Overpass, Geofabrik) | public | 2026-06; ladder 2026-09 | emission surface, static geography |
| Terrain | SRTM / Copernicus DEM | public | 2026-05 | confinement, transport |
| Land cover | ESA WorldCover | public | 2026-09; dispersion benchmark 2026-10-10 | static geography, built-up benchmark |
| Monitoring networks (ladder, spatial tests) | OpenAQ public S3 archive; CNEMC national archive (public mirror) | public | 2026-09 to 2026-10 | ladder and spatial tests |
| Analogue-city stations | OpenAQ, CNEMC, SIATA (Medellín) | public | 2026-03 to 2026-09 | ten-city validation |
| Independent Kandy records | published values (Nirmani et al. 2025; Attanayake et al. 2025; Dhammapala et al. 2022) | published | n/a | level checks |
| NBRO Kandy daily PM2.5, 2021–22 | digitised from Nirmani et al. (2025), CLEAN Soil Air Water, Fig. 3 (place the paper PDF under `references/papers/`) | published figure | 2026-10-11 | daily check at Kandy |
| Regulatory Kandy monitor | Central Environmental Authority | **restricted**: signed agreement; not used | n/a | not used in this thesis |

An authorised reader with PurpleAir access can regenerate the Kandy chain; every cross-city result needs only the
public inputs above.
