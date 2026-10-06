# Pre-registration (DRAFT, not lodged) — the spatial learning curve on full station records

**Status:** draft for the author's approval, 2026-10-04. An extension of OSF `rqn4y` (amendments `26hp8`, `4whsc`,
`4qs9c`), whose registered results (F.119) stand as scored. Lodged before any new PM2.5 is retrieved.

## 1. Question and why
The registered curve drew each candidate site's data from **a single year** (plan step D2), and its freeze
rule kept sites present on at least 75 % of days in the best 365-day window. Within that single year, **21 of 62 candidate cities lost more than half their sites and 14 lost all of them**, and the
tropics were hit hardest: Bangkok kept 11 of 86 sites; Colombia, Mexico, India, Vietnam and two Brazilian
clusters were lost. The registered frame holds one tropical city, which is why it gives no guidance for a city
like Kandy. A single-year window cannot find a better-covered year that a site's longer record may contain. This extension asks what the curve shows when the freeze rule can search each site's **full record**.

## 2. What has been seen, disclosed
The single-year records of all 1,974 candidate locations, and the registered results on the frame they
produced. **No data outside each site's registered year has been retrieved.**

## 3. Design (unchanged from `rqn4y` except the record window)
- **Candidates:** the same 1,974 locations in 67 clusters (`spatial_curve/candidates.csv`).
- **Records:** each location's full archive record (median 3.1 years), retrieved per location with the
  silent-loss audit.
- **Freeze rule, unchanged:** QC, 18-hour site-days, co-located instruments merged, the best 365 consecutive
  days per city, sites present on ≥ 75 % of them; frame rule D3 (primary, secondary, band arm) and the S-1 70 %
  sensitivity frame, unchanged.
- **Predictors:** the registered static predictors and benchmark grids, computed for any newly qualifying site
  by the registered functions (roads from Geofabrik extracts as in D-6).
- **Estimators and scoring:** E0–E7 exactly as registered (nested fitting sets, k sizes, 100 replicates, fixed
  held-out set, cluster bootstrap). **The deep arms (E8–E11) are not re-run** (compute cost; declared now), so X9,
  X10, X11 and X12 are not re-tested.

## 4. Endpoints
- **F1 (the frame):** the number of primary cities and of tropical or deep-tropical cities that qualify, reported
  first, before any curve.
- **F2:** X1–X7 re-evaluated on the full-record frame with the registered rules.
- **F3 (exploratory, declared now):** if three or more tropical or deep-tropical cities qualify, their curves are
  reported separately as a tropical arm (with its own detection limit), against the temperate envelope (as X8).
- Predictions: no direction is predicted for F1. For F2, the registered verdicts are expected to repeat (X2, X3,
  X4, X5, X7 held; X1, X6 refuted), stated here only so that a change is visible.

## 5. What the outcomes would mean
- If tropical cities now qualify, the curve speaks to cities like Kandy for the first time, and the "no station
  count follows" conclusion is revisited with them.
- If they still do not qualify, the scarcity of dense tropical reference networks is a property of the data, not
  of the record window, and the paper says so with that evidence.

## 6. Deviations
Logged with date and reason before scoring.
