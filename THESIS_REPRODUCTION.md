# Reproducing Thesis A

*An hourly kilometre-scale fine particulate matter reconstruction for Kandy, Sri Lanka: construction, validation
without local ground truth, and measurement priorities* (A. M. D. W. B. Alahakoon, University of Peradeniya, 2026).

The submitted version corresponds to the git tag **`thesis-a-2026-10-10`** of this repository. Every number in the
thesis is a token resolved from `kandy_pm25/data/processed/modular/claims.json`, which `build_claims.py` regenerates
from the scored files; the build refuses to produce a document when a stored value and a recomputation disagree.
`VERIFICATION_thesis_a.md` lists every cited claim, its source artefact and whether it rests on public or restricted
inputs. **The pipeline is designed to be reproducible; independent reproduction by a third party has not yet been
carried out.**

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
| Kandy field (T, B, P and the assembled field) | `src/stage1_satml/models/predict_T_anchor_v3.py` → `scripts/sharpen_T_diurnal.py` → `src/stage1_satml/decomp/build_decomp_map.py` → `scripts/build_overlay_predictions.py` → `scripts/build_spatial_uq.py` → `scripts/build_additive_field_v2.py` → `scripts/build_additive_field_v3.py` |
| ten analogue cities | `scripts/xichang_prod.py --city <slug>`, `scripts/city_validation_scorecard.py` |
| information ladder (registered) | `scripts/ladder_v2_confirm.py --score`, `scripts/ladder_v2_rich.py`, `scripts/ladder_v2_learners.py`, `scripts/ladder_v2_fullnet.py` |
| like-for-like and station-count re-analyses (post hoc) | `scripts/ladder_v2_review.py`, `scripts/ladder_v2_review_k.py` |
| deployed model on the ladder (exploratory) | `scripts/pull_kandy_model_priors.py`, `scripts/ladder_v2_kandy_model.py` (spec `kandy_pm25/docs/kandy_model_rung_spec_2026-10-10.md`) |
| humidity scenario | `scripts/kandy_rh_sensitivity.py`, `scripts/kandy_rh_scenario.py` |
| local-fraction sensitivity | `scripts/kandy_f_sensitivity.py` |
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
| Regulatory Kandy monitor | Central Environmental Authority | **restricted**: signed agreement; not used | n/a | not used in this thesis |

An authorised reader with PurpleAir access can regenerate the Kandy chain; every cross-city result needs only the
public inputs above.
