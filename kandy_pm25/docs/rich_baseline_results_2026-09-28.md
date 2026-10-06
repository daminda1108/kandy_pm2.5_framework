# Richer sensorless baseline — registered results (OSF `b379r`, 2026-09-28)

Registration `docs/prereg_rich_baseline_2026-09-28.md` (OSF `b379r`, project `cj9kz`, 12:34:37 UTC). Scored
once on frozen code `831df9a` (manifest re-verified), 119 cities in the frame, **no city excluded** by the
coverage rule. **Parity gate passed:** the base run reproduces the registered confirmation (`ueyfr`) per-city
effects to **2.8e-14**. Output `data/processed/modular/ladder_v2/rich_REGISTERED_*`.

## Registered endpoints (confirmation panel, reconstruction, RMSE unless stated, median [cluster 95 %])

| id | quantity | result | rule | verdict |
|---|---|---|---|---|
| R1 | rich baseline beats base (Bud0 RMSE, %) | **+13.13 [9.20, 16.19]** | lower > 0 | **held** |
| R2 | first two stations, rich baseline | **+8.88 [3.59, 15.28]** | lower > 0 | **held** |
| R3 | paired change in the first-two gain (rich − base) | **−0.69 [−7.07, +1.71]** | upper < 0 | **refuted**: the gain did not shrink detectably |
| R4 | stations 3–6, rich baseline | **+0.24 [0.16, 0.70]** | inside ±1 | **held** |
| R5 | background, rich baseline | **+35.60 [22.07, 58.40]** | lower > 0 | **held** |
| R6 | background − first two, rich (two-sided) | **+21.67 [3.84, 40.65]** | ordering if 0 excluded | **ordering holds: background > first two** |
| R7 | same, exceedance loss | **+45.40 [27.88, 58.27]** | lower > 0 | **held** |

Paired change in H4 (rich − base): −2.83 [−6.34, +3.92]; in H5: −6.43 [−13.05, +3.92] (secondary).
Prospective arm: every verdict the same (R1 +12.29, R2 +5.51 [0.09, 13.01], R6 +20.93 [8.03, 41.77],
R7 +39.27). Discovery panel (secondary): R1 +10.92 [−2.86, +27.78], R2 +17.71, R6 +7.33 [−15.23, +43.01],
R7 +34.02 [0.69, 53.79]. Pooled 118: R1 +12.64, R2 +11.40, R6 +16.27 [1.48, 40.65], R7 +43.64.

## Reading

Adding CAMS PM2.5, terrain, fires, NO2, precipitation and day of week to the sensorless estimate
improves it by about 13 % in the confirmation cities. **Every confirmed verdict survives.** The first two
local stations still add about 9 %, and contrary to the registered prediction their gain does not
measurably shrink: the new streams improve the estimate in ways local stations do not duplicate. The
background still outranks the first two stations for the ordinary day and more clearly for exceedances;
its advantage is slightly smaller (−2.8 and −6.4 points, both intervals including 0). The drop-one
attribution of R1 (declared exploratory) has not been run.
