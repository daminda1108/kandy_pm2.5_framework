# Pre-registration — does the confirmed ladder depend on the station cap?

**Status:** approved by the author 2026-10-04 and lodged before any new PM2.5 was retrieved. Code frozen at commit `1e5f712`; freeze manifest `docs/fullnet_freeze_manifest.json` (SHA-256 `9ad258343899924ca557c2c75aeae1426f70128fdaedff03351588f6be075374`). Related: confirmation OSF `ueyfr`, robustness `b379r` and `jea58`.

## 1. Question and why
Every OpenAQ city in the discovery and confirmation panels entered the ladder with **at most its 12
longest-running stations over its last two calendar years** (`ingest_openaq_sample.py`). The cap binds in 45 of the 63 OpenAQ
confirmation cities (median 17 stations available). In a 12-station city it leaves four held-out stations and
**one or two stations for the background rung**, which carries the confirmed H3, H4 and H5. This test asks
whether the confirmed verdicts survive when every city enters with its full network and full window.

## 2. What has been seen, disclosed
The capped data of every city have been analysed (discovery many times; confirmation once). **No station beyond
the cap and no day outside the capped years has been retrieved.** Retrieval happens only after lodging.

## 3. Data (changes from `ueyfr` only where stated)
- **Cities:** the same discovery (46 scored) and confirmation (72 scored) cities. CNEMC cities already enter with
  all stations; their data are unchanged.
- **OpenAQ stations:** every member location of the city's cluster (`confirmation_members.csv` for confirmation;
  the discovery cluster lists for discovery) ranked by record length, **up to 40** (a few clusters are dense
  low-cost swarms of up to 655 locations; the 40 longest records are kept).
- **Window:** the city's full driver window (confirmation: 2024-09-01 → 2026-08-31; discovery: each city's own
  driver window), not the last two calendar years.
- Hourly QC, the 18-hour station-day rule, equal station weights, the city keep rules (≥ 10 stations, ≥ 200
  driver-matched days, ≥ 120 scored days) and all predictors: **unchanged** (predictor files byte-identical,
  verified by SHA-256 against `docs/confirmation_data_manifest.json` and the ladder v2 freeze).
- Retrieval from the archive's daily objects, atomic per city; the silent-loss audit
  (`confirm_ingest_audit.py`) run on every city before scoring.

## 4. Estimator
Frozen ladder v2 (`e6b744b`, 27 files re-hashed), unchanged: 21 splits, 5 seeds, cross-fitted weights,
two-level cluster bootstrap. The held-out set, background pool and record grow with each city's network.
**Reproduction check (reported, not a gate):** re-applying the old cap (12 stations, last two calendar years)
to the new records should reproduce the registered `ueyfr` per-city effects; any difference (for example from
archive revisions) is reported before the full-network result.

## 5. Endpoints and predictions (confirmation panel, reconstruction, RMSE unless stated)
| id | quantity | rule | prediction |
|---|---|---|---|
| **N1** | H1 first two stations | cluster lower bound > 0 | supported |
| **N2** | H2 stations 3–6 | cluster interval inside [−1, +1] | supported |
| **N3** | H3 background | cluster lower bound > 0 | supported |
| **N4** | H4 background − first two (two-sided) | ordering claimed only if 0 excluded | no direction predicted |
| **N5** | H5 same, exceedance loss | cluster lower bound > 0 | supported |
| **N6** | paired change (full − capped) in H3, H4 and H5 | two-sided, cluster interval | no direction predicted |

Secondary: discovery and pooled panels; prospective arm; tail loss; the number of cities that gain a
background rung; the paired change in H1 and H2.

## 6. What the outcomes would mean
- N3–N5 hold and N6 includes zero: the background verdicts were not an artefact of a one-or-two-station
  background, and the paper says so.
- N6 excludes zero: the size of the background's value depends on how many stations form it; the paper reports
  the full-network value as the better estimate and the capped one as a lower-information version.
- N4 or N5 fails: the ranking of a background above local stations was shaped by the cap, and the paper must
  say so plainly.

## 7. Deviations
Logged with date and reason before scoring.

## 8. Freeze and dry runs (before lodging)
- **Parity gate (passed):** the frozen ladder, re-pointed at a mirror of the original capped station files and of
  every other input (302 files, SHA-256-verified copies), reproduced the registered `ueyfr` per-city effects for
  72 of 72 cities (maximum absolute difference 2.8e-14). Only two path constants are re-pointed; the estimator
  code is untouched.
- **Retrieval check (passed):** one location-year inside the old cap, retrieved by the new code and processed by the
  registered transformation, reproduced the stored record exactly (6,296 of 6,296 hours, difference 0).
- **Retrieval rule:** a location-year is stored only if every listed daily object was retrieved; unparsable objects
  are counted and reported. The silent-loss audit is run before scoring as stated in Section 3.
- **Endpoint N6** compares each city's full-network effect with its registered `ueyfr` value; the same comparison
  against the re-applied cap is reported beside it.
