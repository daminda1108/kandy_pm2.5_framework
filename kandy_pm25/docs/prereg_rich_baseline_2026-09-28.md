# Pre-registration — does the confirmed ladder survive a richer sensorless baseline?

**OSF:** registration [`b379r`](https://osf.io/b379r/), project [`cj9kz`](https://osf.io/cj9kz/), registered
2026-09-28 12:34:37 UTC (pending approval at lodging; a first submission at 12:23 UTC was logged by OSF
but never created, and was re-submitted once from the same draft).

**Status:** approved by the author and lodged on OSF, 2026-09-28, before any result using the new
streams was computed. Code frozen at commit `831df9a`; per-file SHA-256 of 6 code files and all 1,585
predictor files in `docs/rich_freeze_manifest.json` (combined data SHA-256
`35853d7963028378e38f180eb6662743435d35cc855199499b2706b411fb7024`); the ladder v2 freeze (27 files,
`e6b744b`) re-verified unchanged. Dry run on a synthetic outcome passed end to end (the rich rung's
gain on noise: +0.04 [−0.16, +0.19], as it should be).
Related registrations: the ladder v2 confirmation, OSF `ueyfr` (project `dm9zf`), scored 2026-09-28.

## 1. Question and why it is asked now

The confirmation (`ueyfr`) measured what local stations and a background series add to a sensorless
daily estimate built from reanalysis weather, urban-centre geography and MAIAC aerosol optical depth
(rung Bud0c). Every gain on the ladder is measured against the rung below it, so its size depends on
how good that rung is. Bud0c leaves out four kinds of freely available information that a practitioner
would use: a chemical-transport model's PM2.5, which represents regional transport; terrain; fires;
and a dynamic emission proxy. This test asks whether the confirmed findings survive when the
sensorless estimate also has them.

## 2. What has been seen, disclosed in full

- The PM2.5 of every city in this test has already been analysed: the 47 discovery cities many times,
  the 72 confirmation cities once, all with the base rung Bud0c (results in `ueyfr` and ledger F.117).
- **No result using any of the new streams has been computed.** The predictors were pulled before this
  registration (`scripts/rich_streams_pull.py`). The scoring code was tested only on a synthetic
  outcome, independent of every predictor (`ladder_v2_rich.py --dry-run`), and its outputs carry no
  information about any endpoint.
- The predictions below are therefore made knowing the base results. They are not blind to the cities.
  They are blind to the one quantity tested: how the ladder changes when the baseline gains these
  streams.

## 3. Cities (no new selection)

Every city scored in either panel: the 46 discovery cities scored by ladder v2 and the 72 confirmation
cities, 118 in total. No city is chosen by its data. A city is excluded only by this coverage rule, fixed
now: terrain complete, and CAMS, IMERG and FIRMS each present on at least 90 % of the city's frame days.
NO2 and AOD may be missing on any day and are left missing. Excluded cities are named and are also
removed from the base run, so every comparison is on identical cities. Applied to the frame before
lodging (dates and predictors only), the rule excludes **no city** (CAMS ≥ 99.6 % of days in every city;
IMERG and FIRMS complete).
**Primary panel: the confirmation cities**, because the test asks whether the confirmed results
survive. Discovery and pooled results are reported beside them.

## 4. New predictors (Bud0R = Bud0c + these 13 features)

All global, free and computable for a city with no monitors, at the city centroid used by the drivers
(terrain around it). None is sampled at monitor sites.

| stream | feature(s) | source |
|---|---|---|
| chemical-transport PM2.5 | `cams_pm25`: 00 UTC run, forecast hours 0–21, daily mean, 0.4° | ECMWF CAMS global near-real-time (Earth Engine `ECMWF/CAMS/NRT`) |
| dynamic emission proxy | `no2_trop`: tropospheric NO2 column, daily, 5 km | Sentinel-5P TROPOMI OFFL L3 |
| fires | `fire_n100`, `fire_n300`, `fire3_n300`: fire pixels within 100 / 300 km, same day and 3-day sum | FIRMS |
| precipitation | `precip_mm`: daily total, 0.1° | GPM IMERG V07 |
| weekly emission cycle | `dow`: day of week | calendar |
| terrain | `elev_m`, `relief_10`, `relief_30`, `slope_10`, `floor_rel_30`, `enclosure` (8 rays, 15 km, rise ≥ 200 m) | Copernicus GLO-30 DEM with **ocean pixels excluded** by its own water-body mask (sea stored as 0 m would otherwise make a coastal city's relief describe the sea); centroid elevation from land within 500 m, widened to 2 or 5 km where the centroid lies at sea (one city, Dakar); SRTM GL1 only where GLO-30 has no data (Armenia, one city) |

**Contamination check.** The CAMS global system assimilates satellite observations (aerosol optical
depth, O3, CO, NO2, SO2). Its documentation lists no surface PM2.5 or PM10 monitors in any cycle through
50r1 (May 2026), checked 2026-09-28. CAMS therefore does not carry the monitor information that led
us to retire GHAP. CAMS assimilates MODIS AOD, which overlaps with the MAIAC stream already in Bud0c;
that is overlap between free streams, not leakage from monitors.

## 5. Estimator (frozen, unchanged)

The frozen ladder v2 (`ladder_v2.run`, code `e6b744b`) is called by `scripts/ladder_v2_rich.py` twice
on one frame: once with Bud0c's features (**base**) and once with Bud0c plus the 13 features above
(**rich**). Everything else is identical: 21 station splits, 5 learner seeds, cross-fitted weights,
18-hour completeness, leave-one-city-out over all cities in the frame, 4,000-draw two-level cluster
bootstrap. **Parity gate:** before any rich result is written, the base run must reproduce the
registered confirmation's per-city effects to 1e-9; otherwise the run stops. The wrapper's code is frozen
by SHA-256 in `docs/rich_freeze_manifest.json` before lodging (commit `831df9a`).

## 6. Endpoints and predictions (reconstruction arm, RMSE unless stated; confirmation panel)

| id | quantity | rule | prediction |
|---|---|---|---|
| **R1** | rich baseline beats base: % reduction in Bud0 RMSE, per city | cluster lower bound > 0 | **supported** |
| **R2** | H1 under the rich baseline: first two stations | cluster lower bound > 0 | **supported** |
| **R3** | paired change in H1: first-two gain (rich) − (base) | cluster upper bound < 0 | **supported** (the gain shrinks) |
| **R4** | H2 under rich: stations 3–6 | cluster interval inside [−1, +1] | **supported** |
| **R5** | H3 under rich: background given six stations | cluster lower bound > 0 | **supported** |
| **R6** | H4 under rich: background − first two, two-sided | ordering claimed only if the interval excludes 0 | no direction predicted |
| **R7** | H5 under rich: background − first two, exceedance loss | cluster lower bound > 0 | **supported** |

Seven tests; no multiplicity correction; each reported against its own rule.

**Secondary (not counted):** the same quantities on the discovery and pooled panels; the prospective
arm; the tail loss; the paired change in H4 (rich − base), reported with its interval.
**Exploratory, declared now:** which streams carry R1, estimated by dropping one stream group at a time
(CAMS; terrain; fires; NO2; precipitation and day of week) from the rich rung.

## 7. What the outcomes would mean (written before the data)

- R1 fails → the extra streams add nothing once weather, geography and AOD are known, and the confirmed
  ladder stands as measured.
- R2 fails → a city that has good free data gains nothing detectable from its first local stations for
  the daily city mean. The confirmed H1 would then be a statement about weak baselines.
- R6 changes (the confirmed ordering loses its exclusion of zero, or reverses) → the ranking of a
  background above local stations depends on the baseline, and the paper must say so.
- R7 fails → the exceedance advantage of a background series is absorbed by a chemical-transport model,
  and advice to seek a background first applies only to cities without one.

## 8. Deviations

Logged with date and reason before scoring and reported beside the registered result.
