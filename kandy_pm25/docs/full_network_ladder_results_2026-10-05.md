# Test A results — the confirmed ladder on full station networks (OSF `mhgna`), scored once 2026-10-05

Registration `docs/prereg_full_network_ladder_2026-10-04.md` (lodged 2026-10-04 18:22 UTC, project `87znu`).
Code frozen at `1e5f712` (`docs/fullnet_freeze_manifest.json`, verified unchanged before scoring).
Outputs `modular/ladder_v2/fullnet_{original,capped,full}_*`, `fullnet_endpoints.json`. Ledger F.122.

## Data
- Retrieval: 14,135 location-years for A and B together (3.26 M daily objects), every listed object retrieved,
  0 unparsable. Test A: 101 OpenAQ cities (37 discovery, 64 confirmation), all built in both arms.
- Silent-loss audit on all 101 full-network files: median 0.00 %, max 0.04 %, none above 1 %.
- Full arm: median locations used per confirmation city 17 (cap 12); discovery 30 used, 21 with data.
- Confirmation cities scored: **75** (72 under the cap). Three cities newly pass the registered keep rules
  (`oaq_BG_97` reaches 10 stations; `oaq_CZ_109`, `oaq_IT_44` reach 200 driver-matched days); `oaq_IT_115` is
  still dropped (140 days).

## Gates and checks
- **Parity gate (before lodging): passed**, 72/72 cities vs `ueyfr`, max |diff| 2.8e-14.
- **Reproduction check (reported, not a gate):** the old cap re-applied to the new records reproduces the
  confirmation closely but not exactly (69 of 72 per-city vectors differ above 1e-9). Pooled effects:
  H1 +9.39 [3.89, 27.01] vs registered +8.53 [3.07, 25.12]; H2 +0.21 vs +0.22; H3 +40.81 vs +41.10;
  H4 +25.23 [3.27, 47.74] vs +24.58 [4.07, 47.80]; H5 +60.56 vs +59.33. **Cause, measured:** the capped records
  hold no lost rows and no changed values; they hold extra hours. Almost all fall after the driver windows
  (recent accrual) and are removed by the driver merge; **1,313 hourly rows inside the windows across 7 cities**
  are archive back-fill. Because the sensorless rung is one model pooled over all cities, those rows refit
  `Bud0` everywhere, which moves per-city effects slightly in every city. Every verdict is unchanged.

## Registered endpoints (confirmation panel, reconstruction arm, RMSE, median [two-level cluster 95 %])
| id | quantity | full networks | rule | verdict | registered `ueyfr` |
|---|---|---|---|---|---|
| N1 | first two stations | **+7.68 [+3.24, +19.95]**, n 75 | lower > 0 | **SUPPORTED** | +8.53 [3.07, 25.12] |
| N2 | stations 3–6 | **+0.46 [+0.26, +0.73]**, n 75 | inside [−1, +1] | **SUPPORTED** | +0.22 [0.12, 0.50] |
| N3 | background | **+46.02 [+34.26, +63.16]**, n 72 | lower > 0 | **SUPPORTED** | +41.10 [26.77, 62.84] |
| N4 | background − first two | **+32.01 [+11.59, +50.45]**, n 72 | two-sided | **ORDERING: background > first two** | +24.58 [4.07, 47.80] |
| N5 | same, exceedance loss | **+63.38 [+33.54, +71.83]**, n 71 | lower > 0 | **SUPPORTED** | +59.33 [33.93, 67.73] |

**N6, paired change full − registered `ueyfr`, per city (primary, two-sided):**
| quantity | median [cluster 95 %] | n | verdict |
|---|---|---|---|
| H3 background | +0.54 [−1.51, +3.86] | 68 | includes 0 |
| H4 background − first two | **+2.39 [+0.57, +8.91]** | 68 | **excludes 0** |
| H5 same, exceedance | −0.22 [−3.30, +6.30] | 67 | includes 0 |

Against the capped arm (secondary): H3 +0.39 [−1.80, +4.71]; H4 +3.18 [−0.40, +9.54]; H5 +0.00 [−5.44, +7.10],
all including 0.

## Secondary (registered)
- Prospective arm: H1 +6.18 [0.88, 17.87]; H2 +0.59; H3 +48.36 [30.25, 62.79]; H4 +38.56 [15.31, 52.67];
  H5 +58.03 [24.11, 70.17] (registered: +6.46, +0.42, +44.25, +27.31, +50.65).
- Tail loss: first two −4.44 [−9.37, 0.00]; background +51.40 [34.65, 64.89]; H4 +57.27 [29.07, 65.99].
- Cities with a background rung: **72 of 75** (registered 68 of 72); gained: BG_97, CZ_109, IT_44, ZA_105.
- Paired change in H1 −0.80 [−2.92, +0.70] (includes 0); in H2 +0.10 [+0.01, +0.36] (small, excludes 0).
- Discovery panel (union frame, discovery cities scored; original station files → full networks):
  H1 +22.43 [7.43, 39.67] → **+15.22 [6.94, 36.06]**; H2 +0.39 → +0.71 [0.29, 1.30]; H3 +34.21 [15.86, 64.54] →
  **+38.93 [20.45, 65.06]**; H4 +8.65 [−10.04, +43.20] → +12.28 [−2.82, +53.71] (no ordering either way);
  H5 +33.01 [6.94, 60.65] → **+53.95 [24.64, 67.11]**. Same direction as the confirmation panel: the first two
  stations are worth a little less and the background more once the full network is used. (Discovery is
  exploratory; its "original" values differ from the earlier discovery-only run because the union frame also
  trains the sensorless rung on the confirmation cities.)

## What it means (Section 6 of the registration)
- **N3–N5 hold**: the background verdicts were not an artefact of a one- or two-station background. With the
  full networks the background rung is worth slightly more and its ordering above the first two stations is
  stronger (H4 +32.0 vs +24.6).
- **N6 excludes zero for H4 only, by +2.4 points**, against the registered values; against the old cap
  re-applied to the same records it includes zero (+3.2 [−0.4, +9.5]). So part of the registered-vs-full change
  comes from archive back-fill refitting the pooled sensorless rung, not from network size. Per the registration,
  the full-network value is reported as the better estimate and the capped one as a lower-information version;
  the size of the background's advantage depends modestly on how many stations form it, its sign does not.
- Nothing in the confirmed ladder was shaped by the cap in direction or verdict.
