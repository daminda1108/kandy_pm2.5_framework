# Confirmation run (OSF ueyfr) — deviations log

Written before scoring, as section 7 of the registration requires.

## E-1 (2026-09-28 04:45 UTC) — execution only: the OpenAQ ingest runs in 3 disjoint city shards

`ladder_v2_confirm.py --ingest` fetched cities one after another (~10 min per city, ~10 h for 64).
It was stopped after one city (oaq_AM_14, written complete: 12 stations, 122,843 rows) and resumed
with `scripts/confirm_ingest_parallel.py --shard k --n 3`, which runs the identical loop body
(frozen `ingest_openaq_sample.ingest_city`, the same member list, output directory and
skip-if-present rule) on the cities at positions k mod 3 of the same ordering. No data definition,
city rule or estimator changes. The only difference: a per-shard manifest written after every
city (`ingest_manifest_shard{k}.csv`, merged by `--merge`); oaq_AM_14's manifest row, lost with the
stopped process, is re-derived from its parquet.

### E-1 addendum (2026-09-28 06:10 UTC) — the stopped sequential ingest had restarted

Stopping the sequential ingest killed its Python process but not its `retry_until_done.sh` loop,
which restarted it at 04:52 UTC (attempt 2), running beside the three shards until it was killed at
06:09 UTC. It fetched 5 cities that the shards also fetched: oaq_AT_17, oaq_BE_6, oaq_BG_43,
oaq_CA_57, oaq_CZ_113. Both writers ran the same frozen function on the same inputs and reported
identical station and row counts for all five (11/119,158; 10/129,338; 12/137,498; 12/166,444;
10/84,262). Every parquet on disk reads cleanly, holds values in (0, 1000) only and has no duplicate
station-hours. The completeness audit (`confirm_ingest_audit.py`) covers these cities like every
other. No effect on data definitions; recorded for completeness.
